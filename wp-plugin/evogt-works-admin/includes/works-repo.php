<?php
/**
 * Data access for works, files and linked attachments.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

/**
 * Build the WHERE clause and bindings for list/count queries.
 */
function evogt_works_where( array $args ) {
    $where = array( '1=1' );
    $bind  = array();

    $q = isset( $args['s'] ) ? trim( (string) $args['s'] ) : '';
    if ( $q !== '' ) {
        $like    = '%' . addcslashes( $q, '%_\\' ) . '%';
        $where[] = "(w.work_number LIKE :q ESCAPE '\\' OR w.title LIKE :q ESCAPE '\\' OR w.genre LIKE :q ESCAPE '\\' OR w.instrumentation LIKE :q ESCAPE '\\' OR w.comment LIKE :q ESCAPE '\\')";
        $bind[':q'] = $like;
    }

    switch ( isset( $args['filter'] ) ? $args['filter'] : 'all' ) {
        case 'neusatz':      $where[] = '(w.transcription_attachment_id IS NOT NULL OR w.transcription2_attachment_id IS NOT NULL)'; break;
        case 'aufnahme':     $where[] = '(w.audio_attachment_id IS NOT NULL OR w.audio2_attachment_id IS NOT NULL)'; break;
        case 'ausgeblendet': $where[] = 'EXISTS (SELECT 1 FROM files f WHERE f.work_id = w.id AND f.is_public = 0)'; break;
        case 'kommentar':    $where[] = "w.comment IS NOT NULL AND TRIM(w.comment) <> ''"; break;
        case 'ohne_dateien': $where[] = 'NOT EXISTS (SELECT 1 FROM files f WHERE f.work_id = w.id)'; break;
    }

    return array( implode( ' AND ', $where ), $bind );
}

/**
 * Paged list for the admin table.
 * $args: s, filter, orderby (work_number|title), order (asc|desc), per_page, offset
 */
function evogt_works_list( array $args ) {
    $db = evogt_get_db();
    if ( ! $db ) return array();

    list( $where, $bind ) = evogt_works_where( $args );

    $desc     = isset( $args['order'] ) && strtolower( $args['order'] ) === 'desc';
    $by_title = isset( $args['orderby'] ) && $args['orderby'] === 'title';
    $limit    = max( 1, (int) ( isset( $args['per_page'] ) ? $args['per_page'] : 50 ) );
    $offset   = max( 0, (int) ( isset( $args['offset'] ) ? $args['offset'] : 0 ) );

    $select = "SELECT w.id, w.work_number, w.title, w.genre, w.instrumentation,
                      w.transcription_attachment_id, w.transcription2_attachment_id,
                      w.audio_attachment_id, w.audio2_attachment_id,
                      (SELECT COUNT(*) FROM files f WHERE f.work_id = w.id AND f.is_public = 0) AS hidden_count,
                      (w.comment IS NOT NULL AND TRIM(w.comment) <> '') AS has_comment,
                      (SELECT COUNT(*) FROM files f WHERE f.work_id = w.id) AS file_count
               FROM works w
               WHERE $where";

    if ( $by_title ) {
        $stmt = $db->prepare( $select . ' ORDER BY w.title COLLATE NOCASE ' . ( $desc ? 'DESC' : 'ASC' ) . ' LIMIT :limit OFFSET :offset' );
        foreach ( $bind as $k => $v ) $stmt->bindValue( $k, $v );
        $stmt->bindValue( ':limit', $limit, PDO::PARAM_INT );
        $stmt->bindValue( ':offset', $offset, PDO::PARAM_INT );
        $stmt->execute();
        return $stmt->fetchAll( PDO::FETCH_ASSOC );
    }

    // Work numbers are mixed ("9c", "14a", "P-101"), which SQL cannot order
    // naturally. The table is small, so sort in PHP like the front end does.
    $stmt = $db->prepare( $select );
    foreach ( $bind as $k => $v ) $stmt->bindValue( $k, $v );
    $stmt->execute();
    $rows = $stmt->fetchAll( PDO::FETCH_ASSOC );
    usort( $rows, 'evogt_natural_sort_logic' );
    if ( $desc ) $rows = array_reverse( $rows );

    return array_slice( $rows, $offset, $limit );
}

function evogt_works_count( array $args ) {
    $db = evogt_get_db();
    if ( ! $db ) return 0;

    list( $where, $bind ) = evogt_works_where( $args );
    $stmt = $db->prepare( "SELECT COUNT(*) FROM works w WHERE $where" );
    foreach ( $bind as $k => $v ) $stmt->bindValue( $k, $v );
    $stmt->execute();

    return (int) $stmt->fetchColumn();
}

/**
 * One work row (all columns needed by admin and REST) or null.
 */
function evogt_get_work( $id ) {
    $db = evogt_get_db();
    if ( ! $db ) return null;

    $stmt = $db->prepare( 'SELECT id, work_number, title, genre, instrumentation, year, notes, comment,
                                  transcription_attachment_id, transcription2_attachment_id,
                                  audio_attachment_id, audio2_attachment_id, updated_at
                           FROM works WHERE id = ?' );
    $stmt->execute( array( (int) $id ) );
    $work = $stmt->fetch( PDO::FETCH_ASSOC );

    return $work ? $work : null;
}

/**
 * Public URL of an original archive file (flat folder).
 */
function evogt_build_file_url( array $f ) {
    $name = ! empty( $f['flat_path'] ) ? $f['flat_path'] : $f['filename'];
    return EVOGT_PDF_URL . rawurlencode( basename( $name ) );
}

/**
 * Original scans of a work with their saved rotation.
 * Returns [ ['id','filename','url','type','size','rotation','public'], ... ]
 * Scans hidden in the admin area (files.is_public = 0) are left out unless
 * $include_hidden is true (edit screen).
 */
function evogt_get_work_files( $id, $include_hidden = false ) {
    $db = evogt_get_db();
    if ( ! $db ) return array();

    $stmt = $db->prepare( '
        SELECT f.id, f.filename, f.file_type, f.size_bytes, f.flat_path,
               COALESCE(r.rotation, 0) AS rotation,
               COALESCE(f.is_public, 1) AS is_public
        FROM files f
        LEFT JOIN pdf_rotations r ON f.id = r.file_id
        WHERE f.work_id = ?' . ( $include_hidden ? '' : ' AND COALESCE(f.is_public, 1) = 1' ) . '
        ORDER BY f.id' );
    $stmt->execute( array( (int) $id ) );

    $files = array();
    foreach ( $stmt->fetchAll( PDO::FETCH_ASSOC ) as $f ) {
        $files[] = array(
            'id'       => (int) $f['id'],
            'filename' => $f['filename'],
            'url'      => evogt_build_file_url( $f ),
            'type'     => $f['file_type'],
            'size'     => $f['size_bytes'],
            'rotation' => (int) $f['rotation'],
            'public'   => (int) $f['is_public'] === 1,
        );
    }

    return $files;
}

/**
 * Save the editable fields of a work in one transaction.
 * $data: title (string), comment (string|null),
 *        transcription_attachment_id, transcription2_attachment_id,
 *        audio_attachment_id, audio2_attachment_id (int|null),
 *        hidden_file_ids (int[]|null: ids of this work's scans to hide; null = leave unchanged)
 */
function evogt_update_work( $id, array $data ) {
    $db = evogt_get_db();
    if ( ! $db ) {
        return new WP_Error( 'no_db', 'Datenbank nicht gefunden: ' . EVOGT_DB_PATH );
    }

    $int_or_null = function ( $key ) use ( $data ) {
        return ! empty( $data[ $key ] ) ? (int) $data[ $key ] : null;
    };
    $comment = ( isset( $data['comment'] ) && $data['comment'] !== '' ) ? (string) $data['comment'] : null;

    $stmt = $db->prepare( "UPDATE works
                           SET title = :title,
                               comment = :comment,
                               transcription_attachment_id = :t1,
                               transcription2_attachment_id = :t2,
                               audio_attachment_id = :a1,
                               audio2_attachment_id = :a2,
                               updated_at = datetime('now')
                           WHERE id = :id" );
    $stmt->bindValue( ':title', (string) $data['title'] );
    $stmt->bindValue( ':comment', $comment, $comment === null ? PDO::PARAM_NULL : PDO::PARAM_STR );
    foreach ( array( ':t1' => 'transcription_attachment_id', ':t2' => 'transcription2_attachment_id', ':a1' => 'audio_attachment_id', ':a2' => 'audio2_attachment_id' ) as $param => $key ) {
        $v = $int_or_null( $key );
        $stmt->bindValue( $param, $v, $v === null ? PDO::PARAM_NULL : PDO::PARAM_INT );
    }
    $stmt->bindValue( ':id', (int) $id, PDO::PARAM_INT );

    $db->beginTransaction();
    try {
        $stmt->execute();

        if ( isset( $data['hidden_file_ids'] ) && is_array( $data['hidden_file_ids'] ) ) {
            // Unticked checkboxes are not posted: make all scans of this work
            // public first, then hide the ticked ones (scoped to this work).
            $db->prepare( 'UPDATE files SET is_public = 1 WHERE work_id = ?' )->execute( array( (int) $id ) );
            $hide = $db->prepare( 'UPDATE files SET is_public = 0 WHERE work_id = ? AND id = ?' );
            foreach ( array_unique( array_map( 'intval', $data['hidden_file_ids'] ) ) as $file_id ) {
                $hide->execute( array( (int) $id, $file_id ) );
            }
        }

        $db->commit();
    } catch ( PDOException $e ) {
        if ( $db->inTransaction() ) $db->rollBack();
        throw $e;
    }

    delete_transient( 'evogt_all_works' );
    delete_transient( 'evogt_recordings' );

    return true;
}

/**
 * Validate an attachment id against the expected mime type.
 * Returns the id, 0 when empty, or WP_Error when it is not a matching attachment.
 */
function evogt_validate_attachment( $attachment_id, $mime_prefix ) {
    $attachment_id = absint( $attachment_id );
    if ( ! $attachment_id ) return 0;
    if ( get_post_type( $attachment_id ) !== 'attachment' ) {
        return new WP_Error( 'attachment', sprintf( 'Anhang #%d existiert nicht in der Mediathek.', $attachment_id ) );
    }
    $mime = (string) get_post_mime_type( $attachment_id );
    if ( strpos( $mime, $mime_prefix ) !== 0 ) {
        return new WP_Error( 'attachment', sprintf( 'Anhang #%d hat den Typ „%s“, erwartet wird „%s“.', $attachment_id, $mime, $mime_prefix ) );
    }
    return $attachment_id;
}

/**
 * Attachment as the front end expects it (same shape as the former media map).
 * $kind: 'transcription' (PDF) or 'audio'. Returns null for dangling/mismatching ids.
 */
function evogt_attachment_item( $attachment_id, $kind ) {
    $attachment_id = (int) $attachment_id;
    if ( ! $attachment_id || get_post_type( $attachment_id ) !== 'attachment' ) return null;

    $mime = (string) get_post_mime_type( $attachment_id );
    if ( $kind === 'audio' ? strpos( $mime, 'audio/' ) !== 0 : $mime !== 'application/pdf' ) return null;

    $url = wp_get_attachment_url( $attachment_id );
    if ( ! $url ) return null;

    $post = get_post( $attachment_id );
    $meta = wp_get_attachment_metadata( $attachment_id );
    $item = array(
        'attachment_id' => $attachment_id,
        'title'         => $post ? $post->post_title : basename( $url ),
        'url'           => $url,
        'date'          => $post ? $post->post_date : '',
    );

    if ( $kind === 'audio' ) {
        $item['length_formatted'] = isset( $meta['length_formatted'] ) ? $meta['length_formatted'] : '';
    } else {
        $size = isset( $meta['filesize'] ) ? (int) $meta['filesize'] : 0;
        if ( ! $size ) {
            $file = get_attached_file( $attachment_id );
            if ( $file && file_exists( $file ) ) $size = filesize( $file );
        }
        $item['size'] = $size;
    }

    return $item;
}

/**
 * delete_attachment: remove references to an attachment that is being deleted.
 */
function evogt_detach_attachment( $attachment_id ) {
    $db = evogt_get_db();
    if ( ! $db ) return;
    try {
        $cols = evogt_table_columns( $db, 'works' );
        if ( ! in_array( 'audio_attachment_id', $cols, true ) ) return;
        foreach ( array( 'transcription_attachment_id', 'transcription2_attachment_id', 'audio_attachment_id', 'audio2_attachment_id' ) as $col ) {
            if ( ! in_array( $col, $cols, true ) ) continue;
            $db->prepare( "UPDATE works SET $col = NULL, updated_at = datetime('now') WHERE $col = ?" )->execute( array( (int) $attachment_id ) );
        }
        delete_transient( 'evogt_recordings' );
    } catch ( PDOException $e ) {
        error_log( 'evogt: detach attachment failed: ' . $e->getMessage() );
    }
}
