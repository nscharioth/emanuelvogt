<?php
/**
 * One-time import of media that were linked to works via the media-library
 * caption (caption == filename of an original archive file).
 */

if ( ! defined( 'ABSPATH' ) ) exit;

/**
 * Fill empty transcription/audio slots from caption-linked attachments.
 * Only NULL columns are written, so re-running never overwrites manual choices.
 *
 * @return array|WP_Error ['migrated' => int, 'skipped' => int, 'log' => string[]]
 */
function evogt_migrate_caption_media( $force = false ) {
    if ( get_option( 'evogt_media_migrated' ) && ! $force ) {
        return new WP_Error( 'done', 'Die Medien wurden bereits übernommen.' );
    }

    $db = evogt_get_db();
    if ( ! $db ) {
        return new WP_Error( 'no_db', 'Datenbank nicht gefunden: ' . EVOGT_DB_PATH );
    }

    global $wpdb;
    $rows = $wpdb->get_results(
        "SELECT ID, post_title, post_excerpt, post_mime_type, post_date
         FROM {$wpdb->posts}
         WHERE post_type = 'attachment'
           AND (post_mime_type = 'application/pdf' OR post_mime_type LIKE 'audio/%')
           AND post_excerpt <> ''
         ORDER BY post_date DESC",
        ARRAY_A
    );

    $log      = array();
    $migrated = 0;
    $skipped  = 0;

    try {
        // LOWER(TRIM(filename)) => work_id
        $file_to_work = array();
        foreach ( $db->query( 'SELECT LOWER(TRIM(filename)) AS fn, work_id FROM files WHERE work_id IS NOT NULL' ) as $f ) {
            if ( ! isset( $file_to_work[ $f['fn'] ] ) ) {
                $file_to_work[ $f['fn'] ] = (int) $f['work_id'];
            }
        }

        // Rows are newest first, so the first attachment per work and kind wins.
        $assign = array();
        foreach ( $rows as $r ) {
            $key  = strtolower( trim( $r['post_excerpt'] ) );
            $kind = strpos( $r['post_mime_type'], 'audio/' ) === 0 ? 'audio' : 'transcription';
            $id   = (int) $r['ID'];

            if ( empty( $file_to_work[ $key ] ) ) {
                $skipped++;
                $log[] = sprintf( 'Übersprungen: Anhang #%d (%s) – Kurzbeschreibung „%s“ passt zu keiner Archivdatei.', $id, $r['post_title'], $key );
                continue;
            }
            $wid = $file_to_work[ $key ];
            if ( isset( $assign[ $wid ][ $kind ] ) ) {
                $skipped++;
                $log[] = sprintf( 'Übersprungen: Anhang #%d – Werk %d hat bereits einen neueren %s (#%d).', $id, $wid, $kind === 'audio' ? 'Aufnahme-Anhang' : 'Neusatz-Anhang', $assign[ $wid ][ $kind ] );
                continue;
            }
            $assign[ $wid ][ $kind ] = $id;
        }

        $up = array(
            'transcription' => $db->prepare( "UPDATE works SET transcription_attachment_id = ?, updated_at = datetime('now') WHERE id = ? AND transcription_attachment_id IS NULL" ),
            'audio'         => $db->prepare( "UPDATE works SET audio_attachment_id = ?, updated_at = datetime('now') WHERE id = ? AND audio_attachment_id IS NULL" ),
        );

        $db->beginTransaction();
        foreach ( $assign as $wid => $kinds ) {
            foreach ( $kinds as $kind => $attachment_id ) {
                $up[ $kind ]->execute( array( $attachment_id, $wid ) );
                if ( $up[ $kind ]->rowCount() > 0 ) {
                    $migrated++;
                    $log[] = sprintf( 'Werk %d ← %s #%d', $wid, $kind === 'audio' ? 'Aufnahme' : 'Neusatz', $attachment_id );
                } else {
                    $skipped++;
                    $log[] = sprintf( 'Übersprungen: Werk %d hat bereits einen %s gesetzt (Anhang #%d nicht übernommen).', $wid, $kind === 'audio' ? 'Aufnahme-Anhang' : 'Neusatz-Anhang', $attachment_id );
                }
            }
        }
        $db->commit();
    } catch ( PDOException $e ) {
        if ( $db->inTransaction() ) $db->rollBack();
        error_log( 'evogt: media migration failed: ' . $e->getMessage() );
        return new WP_Error( 'db_error', 'Medienübernahme fehlgeschlagen: ' . $e->getMessage() );
    }

    update_option( 'evogt_media_migrated', array(
        'at'       => current_time( 'mysql' ),
        'migrated' => $migrated,
        'skipped'  => $skipped,
        'total'    => count( $rows ),
    ) );
    update_option( 'evogt_media_migration_log', array_slice( $log, 0, 500 ), false );

    delete_transient( 'evogt_all_works' );
    delete_transient( 'evogt_recordings' );
    error_log( "evogt: media migration migrated=$migrated skipped=$skipped" );

    return array( 'migrated' => $migrated, 'skipped' => $skipped, 'log' => $log );
}
