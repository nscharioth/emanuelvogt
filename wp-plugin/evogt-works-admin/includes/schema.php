<?php
/**
 * Idempotent schema migration of the SQLite works table.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

const EVOGT_SCHEMA_VERSION = 2;

/**
 * Columns added by this plugin => ALTER statement.
 * Note: SQLite does not allow non-constant defaults in ALTER TABLE, so
 * updated_at has no default; every UPDATE sets datetime('now') explicitly.
 */
function evogt_schema_columns() {
    return array(
        'comment'                     => 'ALTER TABLE works ADD COLUMN comment TEXT',
        'transcription_attachment_id' => 'ALTER TABLE works ADD COLUMN transcription_attachment_id INTEGER',
        'audio_attachment_id'         => 'ALTER TABLE works ADD COLUMN audio_attachment_id INTEGER',
        'updated_at'                  => 'ALTER TABLE works ADD COLUMN updated_at TEXT',
        // Schema version 2: second transcribed PDF and second recording per work
        'transcription2_attachment_id' => 'ALTER TABLE works ADD COLUMN transcription2_attachment_id INTEGER',
        'audio2_attachment_id'         => 'ALTER TABLE works ADD COLUMN audio2_attachment_id INTEGER',
    );
}

/**
 * Add missing columns (after a backup). Returns ['added' => [], 'backup' => path|null] or WP_Error.
 */
function evogt_schema_migrate( $backup = true ) {
    $db = evogt_get_db();
    if ( ! $db ) {
        return new WP_Error( 'no_db', 'Datenbank nicht gefunden oder SQLite-Treiber fehlt: ' . EVOGT_DB_PATH );
    }

    try {
        $existing = evogt_table_columns( $db, 'works' );
    } catch ( PDOException $e ) {
        return new WP_Error( 'pragma_failed', 'Schema konnte nicht gelesen werden: ' . $e->getMessage() );
    }
    if ( ! $existing ) {
        return new WP_Error( 'no_works_table', 'Die Tabelle "works" fehlt in der Datenbank.' );
    }

    $missing = array_diff_key( evogt_schema_columns(), array_flip( $existing ) );
    if ( ! $missing ) {
        update_option( 'evogt_schema_version', EVOGT_SCHEMA_VERSION );
        return array( 'added' => array(), 'backup' => null );
    }

    if ( ! wp_is_writable( EVOGT_DB_PATH ) || ! wp_is_writable( dirname( EVOGT_DB_PATH ) ) ) {
        return new WP_Error( 'not_writable', 'Datenbank oder Datenverzeichnis sind nicht beschreibbar: ' . EVOGT_DB_PATH );
    }

    $bak = null;
    if ( $backup ) {
        $bak = evogt_backup_db( 'schema' );
        if ( is_wp_error( $bak ) ) return $bak; // no backup, no migration
    }

    try {
        $db->beginTransaction();
        foreach ( $missing as $sql ) {
            $db->exec( $sql );
        }
        $db->commit();
        $db->exec( 'CREATE INDEX IF NOT EXISTS idx_works_audio_attachment ON works(audio_attachment_id)' );
        $db->exec( 'CREATE INDEX IF NOT EXISTS idx_works_audio2_attachment ON works(audio2_attachment_id)' );
    } catch ( PDOException $e ) {
        if ( $db->inTransaction() ) $db->rollBack();
        return new WP_Error( 'alter_failed', 'Schema-Migration fehlgeschlagen: ' . $e->getMessage() );
    }

    update_option( 'evogt_schema_version', EVOGT_SCHEMA_VERSION );
    delete_transient( 'evogt_all_works' );
    delete_transient( 'evogt_recordings' );

    return array( 'added' => array_keys( $missing ), 'backup' => $bak );
}

/**
 * admin_init: re-check the schema whenever the database file changed
 * (e.g. a freshly uploaded archive.db), at most once per hour otherwise.
 */
function evogt_maybe_migrate_schema() {
    if ( wp_doing_ajax() || ! current_user_can( EVOGT_CAP ) ) return;
    if ( ! file_exists( EVOGT_DB_PATH ) ) return;

    $stamp = EVOGT_SCHEMA_VERSION . ':' . filemtime( EVOGT_DB_PATH ) . ':' . filesize( EVOGT_DB_PATH );
    if ( get_transient( 'evogt_schema_checked' ) === $stamp ) return;

    $result = evogt_schema_migrate();
    if ( is_wp_error( $result ) ) {
        set_transient( 'evogt_admin_flash', array( 'type' => 'error', 'msg' => $result->get_error_message() ), MINUTE_IN_SECONDS );
        return;
    }

    if ( $result['added'] ) {
        set_transient( 'evogt_admin_flash', array(
            'type' => 'success',
            'msg'  => 'Datenbank-Schema aktualisiert (' . implode( ', ', $result['added'] ) . '). Sicherung: ' . basename( $result['backup'] ),
        ), MINUTE_IN_SECONDS );
    }

    // Covers the case where the DB was missing at activation time.
    if ( ! get_option( 'evogt_media_migrated' ) ) {
        evogt_migrate_caption_media();
    }

    // The migration itself changed mtime/size, so stamp the file as it is now.
    clearstatcache( true, EVOGT_DB_PATH );
    set_transient( 'evogt_schema_checked', EVOGT_SCHEMA_VERSION . ':' . filemtime( EVOGT_DB_PATH ) . ':' . filesize( EVOGT_DB_PATH ), HOUR_IN_SECONDS );
}

/**
 * init: after a plugin update by upload the activation hook does not run.
 * Migrate on the first request (front end or admin) whenever the stored
 * schema version is behind, so REST never queries missing columns.
 * A failed attempt is retried at most every 5 minutes.
 */
function evogt_upgrade_schema_on_init() {
    if ( (int) get_option( 'evogt_schema_version', 0 ) >= EVOGT_SCHEMA_VERSION ) return;
    if ( ! file_exists( EVOGT_DB_PATH ) || get_transient( 'evogt_schema_upgrade_failed' ) ) return;

    $result = evogt_schema_migrate();
    if ( is_wp_error( $result ) ) {
        error_log( 'evogt: schema upgrade failed: ' . $result->get_error_message() );
        set_transient( 'evogt_schema_upgrade_failed', 1, 5 * MINUTE_IN_SECONDS );
        return;
    }
    delete_transient( 'evogt_schema_checked' );
}
