<?php
/**
 * SQLite connection, status and backup helpers.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

/**
 * One PDO connection per request. Returns null (never throws) when the
 * sqlite driver or the database file is missing.
 */
function evogt_get_db() {
    static $db = null;
    static $failed = false;

    if ( $db instanceof PDO ) return $db;
    if ( $failed ) return null;

    if ( ! class_exists( 'PDO' ) || ! in_array( 'sqlite', PDO::getAvailableDrivers(), true ) ) {
        $failed = true;
        return null;
    }
    if ( ! file_exists( EVOGT_DB_PATH ) ) {
        $failed = true;
        return null;
    }

    try {
        $db = new PDO( 'sqlite:' . EVOGT_DB_PATH );
        $db->setAttribute( PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION );
        $db->setAttribute( PDO::ATTR_TIMEOUT, 5 ); // busy timeout in seconds
    } catch ( PDOException $e ) {
        error_log( 'evogt: could not open archive.db: ' . $e->getMessage() );
        $failed = true;
        $db = null;
    }

    return $db;
}

/**
 * Column names of a table (empty array when the table does not exist).
 */
function evogt_table_columns( PDO $db, $table ) {
    $cols = array();
    foreach ( $db->query( 'PRAGMA table_info(' . $table . ')' )->fetchAll( PDO::FETCH_ASSOC ) as $col ) {
        $cols[] = $col['name'];
    }
    return $cols;
}

/**
 * Status of the archive database for notices and the tools page.
 */
function evogt_db_status() {
    $path   = EVOGT_DB_PATH;
    $dir    = dirname( $path );
    $status = array(
        'path'           => $path,
        'pdo_sqlite'     => class_exists( 'PDO' ) && in_array( 'sqlite', PDO::getAvailableDrivers(), true ),
        'exists'         => file_exists( $path ),
        'writable'       => file_exists( $path ) && wp_is_writable( $path ),
        'dir_writable'   => is_dir( $dir ) && wp_is_writable( $dir ),
        'size'           => file_exists( $path ) ? filesize( $path ) : 0,
        'mtime'          => file_exists( $path ) ? filemtime( $path ) : 0,
        'sqlite_version' => '',
        'schema_ok'      => false,
        'missing'        => array(),
        'works'          => null,
    );

    $db = evogt_get_db();
    if ( $db ) {
        try {
            $status['sqlite_version'] = (string) $db->query( 'SELECT sqlite_version()' )->fetchColumn();
            $missing = array_diff( array_keys( evogt_schema_columns() ), evogt_table_columns( $db, 'works' ) );
            $status['missing']   = array_values( $missing );
            $status['schema_ok'] = empty( $missing );
            $status['works']     = (int) $db->query( 'SELECT COUNT(*) FROM works' )->fetchColumn();
        } catch ( PDOException $e ) {
            error_log( 'evogt: status query failed: ' . $e->getMessage() );
        }
    }

    return $status;
}

/**
 * Copy archive.db to archive.db.bak-YYYYmmdd-HHMMSS[-label] next to it and
 * keep only the newest 10 backups. Returns the backup path or WP_Error.
 */
function evogt_backup_db( $label = '' ) {
    if ( ! file_exists( EVOGT_DB_PATH ) ) {
        return new WP_Error( 'no_db', 'Datenbank nicht gefunden: ' . EVOGT_DB_PATH );
    }
    $dir = dirname( EVOGT_DB_PATH );
    if ( ! wp_is_writable( $dir ) ) {
        return new WP_Error( 'dir_not_writable', 'Das Datenverzeichnis ist nicht beschreibbar, Sicherung nicht möglich: ' . $dir );
    }

    $target = EVOGT_DB_PATH . '.bak-' . gmdate( 'Ymd-His' ) . ( $label ? '-' . sanitize_key( $label ) : '' );
    if ( ! copy( EVOGT_DB_PATH, $target ) ) {
        return new WP_Error( 'copy_failed', 'Sicherungskopie konnte nicht angelegt werden: ' . $target );
    }

    // Prune: keep the newest 10 backups.
    $backups = evogt_list_backups();
    foreach ( array_slice( $backups, 10 ) as $old ) {
        @unlink( $old['path'] );
    }

    return $target;
}

/**
 * Existing backups, newest first: [ ['path','name','size','mtime'], ... ].
 */
function evogt_list_backups() {
    $files = glob( EVOGT_DB_PATH . '.bak-*' );
    if ( ! $files ) return array();
    $list = array();
    foreach ( $files as $f ) {
        $list[] = array( 'path' => $f, 'name' => basename( $f ), 'size' => filesize( $f ), 'mtime' => filemtime( $f ) );
    }
    usort( $list, function ( $a, $b ) { return $b['mtime'] - $a['mtime']; } );
    return $list;
}

/**
 * Deny web access to the database, journals and backups (Apache). Written
 * once when missing; other servers need an equivalent rule (see tools page).
 */
function evogt_write_htaccess_guard() {
    $dir = dirname( EVOGT_DB_PATH );
    if ( ! is_dir( $dir ) || ! wp_is_writable( $dir ) ) return false;
    $file = $dir . '/.htaccess';
    if ( file_exists( $file ) ) return true;
    $rules = "# Added by EmanuelVogt Werkverzeichnis: never serve the archive database over HTTP\n"
           . "<FilesMatch \"\\.(db|db-journal|db-wal|db-shm|bak-.*|download-tmp)$\">\n"
           . "  <IfModule mod_authz_core.c>\n    Require all denied\n  </IfModule>\n"
           . "  <IfModule !mod_authz_core.c>\n    Order deny,allow\n    Deny from all\n  </IfModule>\n"
           . "</FilesMatch>\n";
    return (bool) file_put_contents( $file, $rules );
}

/**
 * Natural order for work numbers such as 1, 2, 9c, 14, 14a, 1975.
 */
function evogt_natural_sort_logic( $a, $b ) {
    return strnatcasecmp( isset( $a['work_number'] ) ? $a['work_number'] : '', isset( $b['work_number'] ) ? $b['work_number'] : '' );
}
