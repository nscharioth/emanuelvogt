<?php
/**
 * REST API evogt/v1 (moved from the theme). Routes and permissions are
 * unchanged so the front-end app keeps working without modification.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

function evogt_register_rest_routes() {
    register_rest_route( 'evogt/v1', '/works', array(
        'methods'             => 'GET',
        'callback'            => 'evogt_api_get_works',
        'permission_callback' => '__return_true',
    ) );

    register_rest_route( 'evogt/v1', '/work/(?P<id>\d+)', array(
        'methods'             => 'GET',
        'callback'            => 'evogt_api_get_work',
        'permission_callback' => '__return_true',
    ) );

    register_rest_route( 'evogt/v1', '/genres', array(
        'methods'             => 'GET',
        'callback'            => 'evogt_api_get_genres',
        'permission_callback' => '__return_true',
    ) );

    register_rest_route( 'evogt/v1', '/instrumentations', array(
        'methods'             => 'GET',
        'callback'            => 'evogt_api_get_instrumentations',
        'permission_callback' => '__return_true',
    ) );

    register_rest_route( 'evogt/v1', '/pdf-rotation/(?P<file_id>\d+)', array(
        'methods'             => 'GET',
        'callback'            => 'evogt_api_get_pdf_rotation',
        'permission_callback' => '__return_true',
    ) );

    register_rest_route( 'evogt/v1', '/pdf-rotation/(?P<file_id>\d+)', array(
        'methods'             => 'POST',
        'callback'            => 'evogt_api_set_pdf_rotation',
        'permission_callback' => function () {
            return current_user_can( EVOGT_CAP );
        },
    ) );

    register_rest_route( 'evogt/v1', '/recordings', array(
        'methods'             => 'GET',
        'callback'            => 'evogt_api_get_recordings',
        'permission_callback' => '__return_true',
    ) );
}

/** Shared error responses. */
function evogt_rest_no_db() {
    return new WP_Error( 'evogt_no_db', 'Datenbank nicht gefunden', array( 'status' => 500 ) );
}
function evogt_rest_db_error( PDOException $e ) {
    error_log( 'evogt REST: ' . $e->getMessage() );
    return new WP_Error( 'evogt_db_error', 'Datenbankfehler', array( 'status' => 500 ) );
}

function evogt_api_get_works( $request ) {
    $db = evogt_get_db();
    if ( ! $db ) return evogt_rest_no_db();

    $q = sanitize_text_field( trim( (string) $request->get_param( 'q' ) ) );

    try {
        if ( $q === '' ) {
            // No search query: serve from transient cache (5-min TTL)
            $rows = get_transient( 'evogt_all_works' );
            if ( $rows === false ) {
                $rows = $db->query( 'SELECT id, work_number, title, genre, instrumentation FROM works ORDER BY work_number' )->fetchAll( PDO::FETCH_ASSOC );
                usort( $rows, 'evogt_natural_sort_logic' );
                set_transient( 'evogt_all_works', $rows, 5 * MINUTE_IN_SECONDS );
            }
        } else {
            $like = '%' . $q . '%';
            $stmt = $db->prepare(
                'SELECT id, work_number, title, genre, instrumentation FROM works
                 WHERE title LIKE ? OR work_number LIKE ? OR genre LIKE ? OR instrumentation LIKE ?'
            );
            $stmt->execute( array( $like, $like, $like, $like ) );
            $rows = $stmt->fetchAll( PDO::FETCH_ASSOC );
            usort( $rows, 'evogt_natural_sort_logic' );
        }
    } catch ( PDOException $e ) {
        return evogt_rest_db_error( $e );
    }

    return new WP_REST_Response( $rows, 200 );
}

function evogt_api_get_work( $request ) {
    $db = evogt_get_db();
    if ( ! $db ) return evogt_rest_no_db();

    $id = intval( $request->get_param( 'id' ) );

    try {
        $work = evogt_get_work( $id );
        if ( ! $work ) {
            return new WP_Error( 'evogt_not_found', 'Not found', array( 'status' => 404 ) );
        }
        $files = evogt_get_work_files( $id );
    } catch ( PDOException $e ) {
        return evogt_rest_db_error( $e );
    }

    $out = array(
        'id'              => (int) $work['id'],
        'work_number'     => $work['work_number'],
        'title'           => $work['title'],
        'genre'           => $work['genre'],
        'instrumentation' => $work['instrumentation'],
        'files'           => $files,
    );

    $comment        = isset( $work['comment'] ) ? trim( (string) $work['comment'] ) : '';
    $out['comment'] = $comment !== '' ? wp_kses_post( wpautop( $comment ) ) : '';

    // Up to two transcribed PDFs and two recordings, slot 1 first.
    $out['transcriptions'] = evogt_work_attachments( $work, array( 'transcription_attachment_id', 'transcription2_attachment_id' ), 'transcription' );
    $out['audio']          = evogt_work_attachments( $work, array( 'audio_attachment_id', 'audio2_attachment_id' ), 'audio' );

    return new WP_REST_Response( $out, 200 );
}

/**
 * Attachment items for the given slot columns, skipping empty or dangling ids.
 */
function evogt_work_attachments( array $work, array $columns, $kind ) {
    $items = array();
    foreach ( $columns as $col ) {
        $item = evogt_attachment_item( isset( $work[ $col ] ) ? $work[ $col ] : 0, $kind );
        if ( $item ) $items[] = $item;
    }
    return $items;
}

/**
 * Works with a linked recording, newest recording first (feeds the "Aufnahmen" tiles).
 */
function evogt_api_get_recordings() {
    $db = evogt_get_db();
    if ( ! $db ) return evogt_rest_no_db();

    $recordings = get_transient( 'evogt_recordings' );
    if ( $recordings !== false ) {
        return new WP_REST_Response( $recordings, 200 );
    }

    try {
        if ( ! in_array( 'audio2_attachment_id', evogt_table_columns( $db, 'works' ), true ) ) {
            return new WP_REST_Response( array(), 200 ); // schema not migrated yet
        }
        $rows = $db->query( 'SELECT id, work_number, title, genre, audio_attachment_id, audio2_attachment_id FROM works
                             WHERE audio_attachment_id IS NOT NULL OR audio2_attachment_id IS NOT NULL' )
                   ->fetchAll( PDO::FETCH_ASSOC );
    } catch ( PDOException $e ) {
        return evogt_rest_db_error( $e );
    }

    $recordings = array();
    foreach ( $rows as $row ) {
      foreach ( array( 'audio_attachment_id', 'audio2_attachment_id' ) as $col ) {
        if ( empty( $row[ $col ] ) ) continue;
        $audio = evogt_attachment_item( $row[ $col ], 'audio' );
        if ( ! $audio ) {
            error_log( 'evogt: work ' . $row['id'] . ' references missing audio attachment #' . $row[ $col ] );
            continue;
        }
        $recordings[] = array(
            'work_id'          => (int) $row['id'],
            'work_number'      => $row['work_number'],
            'title'            => $row['title'],
            'genre'            => $row['genre'],
            'audio_url'        => $audio['url'],
            'length_formatted' => $audio['length_formatted'],
            'date'             => $audio['date'],
        );
      }
    }

    usort( $recordings, function ( $a, $b ) { return strcmp( $b['date'], $a['date'] ); } );
    set_transient( 'evogt_recordings', $recordings, 5 * MINUTE_IN_SECONDS );

    return new WP_REST_Response( $recordings, 200 );
}

function evogt_api_get_genres() {
    $db = evogt_get_db();
    if ( ! $db ) return evogt_rest_no_db();

    try {
        $rows = $db->query( 'SELECT DISTINCT genre FROM works WHERE genre IS NOT NULL' )->fetchAll( PDO::FETCH_COLUMN );
    } catch ( PDOException $e ) {
        return evogt_rest_db_error( $e );
    }

    $genres = array_merge( array( 'All' ), $rows );
    return new WP_REST_Response( array_values( array_unique( $genres ) ), 200 );
}

function evogt_api_get_instrumentations() {
    $db = evogt_get_db();
    if ( ! $db ) return evogt_rest_no_db();

    try {
        $rows = $db->query( 'SELECT DISTINCT instrumentation FROM works WHERE instrumentation IS NOT NULL' )->fetchAll( PDO::FETCH_COLUMN );
    } catch ( PDOException $e ) {
        return evogt_rest_db_error( $e );
    }

    $all = array();
    foreach ( $rows as $inst ) {
        if ( ! $inst ) continue;
        foreach ( explode( ',', $inst ) as $p ) {
            $all[] = trim( $p );
        }
    }
    $unique = array_unique( $all );
    sort( $unique );
    array_unshift( $unique, 'All' );

    return new WP_REST_Response( $unique, 200 );
}

function evogt_api_get_pdf_rotation( $request ) {
    $db = evogt_get_db();
    if ( ! $db ) return evogt_rest_no_db();
    $file_id = intval( $request->get_param( 'file_id' ) );

    try {
        $stmt = $db->prepare( 'SELECT rotation FROM pdf_rotations WHERE file_id = ?' );
        $stmt->execute( array( $file_id ) );
        $res = $stmt->fetchColumn();
    } catch ( PDOException $e ) {
        return evogt_rest_db_error( $e );
    }

    return new WP_REST_Response( array( 'file_id' => $file_id, 'rotation' => $res !== false ? intval( $res ) : 0 ), 200 );
}

function evogt_api_set_pdf_rotation( $request ) {
    if ( ! current_user_can( EVOGT_CAP ) ) {
        return new WP_Error( 'evogt_forbidden', 'Unauthorized', array( 'status' => 403 ) );
    }

    $db = evogt_get_db();
    if ( ! $db ) return evogt_rest_no_db();

    $file_id  = intval( $request->get_param( 'file_id' ) );
    $params   = $request->get_json_params();
    $rotation = intval( isset( $params['rotation'] ) ? $params['rotation'] : 0 );

    if ( ! in_array( $rotation, array( 0, 90, 180, 270 ), true ) ) {
        return new WP_Error( 'evogt_invalid_rotation', 'Invalid rotation', array( 'status' => 400 ) );
    }

    try {
        $stmt = $db->prepare( 'INSERT OR REPLACE INTO pdf_rotations (file_id, rotation, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)' );
        $stmt->execute( array( $file_id, $rotation ) );
    } catch ( PDOException $e ) {
        return evogt_rest_db_error( $e );
    }

    return new WP_REST_Response( array( 'file_id' => $file_id, 'rotation' => $rotation, 'saved' => true ), 200 );
}

/**
 * The hosting adds long cache lifetimes (weeks) to responses without explicit
 * headers, so edits made in the admin area would not show up. Forbid caching
 * of every evogt/v1 response in browsers and proxies.
 */
function evogt_rest_nocache_headers( $response, $server, $request ) {
    if ( strpos( $request->get_route(), '/evogt/v1' ) !== 0 || ! ( $response instanceof WP_HTTP_Response ) ) {
        return $response;
    }
    $response->header( 'Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0' );
    $response->header( 'Expires', 'Wed, 11 Jan 1984 05:00:00 GMT' );
    $response->header( 'Pragma', 'no-cache' );
    return $response;
}
add_filter( 'rest_post_dispatch', 'evogt_rest_nocache_headers', 10, 3 );
