<?php
/**
 * "Werkzeuge": database status, backup download, migrations.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

add_action( 'admin_post_evogt_download_db', 'evogt_handle_download_db' );
add_action( 'admin_post_evogt_rerun_media_migration', 'evogt_handle_rerun_media_migration' );
add_action( 'admin_post_evogt_run_schema_migration', 'evogt_handle_run_schema_migration' );

function evogt_tools_url() {
    return add_query_arg( array( 'page' => 'evogt-tools' ), admin_url( 'admin.php' ) );
}

function evogt_render_tools_page() {
    if ( ! current_user_can( EVOGT_CAP ) ) wp_die( 'Keine Berechtigung.', 403 );

    $status  = evogt_db_status();
    $counts  = array( 'neusatz' => 0, 'aufnahme' => 0, 'kommentar' => 0, 'ohne_dateien' => 0 );
    if ( $status['schema_ok'] ) {
        foreach ( array_keys( $counts ) as $k ) $counts[ $k ] = evogt_works_count( array( 'filter' => $k ) );
    }
    $migrated = get_option( 'evogt_media_migrated' );
    $log      = get_option( 'evogt_media_migration_log', array() );
    $backups  = evogt_list_backups();
    $is_apache = isset( $_SERVER['SERVER_SOFTWARE'] ) && stripos( $_SERVER['SERVER_SOFTWARE'], 'apache' ) !== false;
    ?>
    <div class="wrap evogt-wrap">
        <h1>Werkzeuge</h1>

        <h2>Datenbank</h2>
        <table class="widefat striped evogt-status-table">
            <tbody>
                <tr><th>Pfad</th><td><code><?php echo esc_html( $status['path'] ); ?></code></td></tr>
                <tr><th>SQLite-Treiber (pdo_sqlite)</th><td><?php echo $status['pdo_sqlite'] ? 'vorhanden' : '<strong>fehlt</strong>'; ?></td></tr>
                <tr><th>Datei vorhanden</th><td><?php echo $status['exists'] ? 'ja' : '<strong>nein</strong>'; ?></td></tr>
                <tr><th>Datei beschreibbar</th><td><?php echo $status['writable'] ? 'ja' : '<strong>nein</strong>'; ?></td></tr>
                <tr><th>Verzeichnis beschreibbar (für Sicherungen)</th><td><?php echo $status['dir_writable'] ? 'ja' : '<strong>nein</strong>'; ?></td></tr>
                <tr><th>Größe / geändert</th><td><?php echo $status['exists'] ? esc_html( size_format( $status['size'], 1 ) . ' / ' . wp_date( 'd.m.Y H:i', $status['mtime'] ) ) : '–'; ?></td></tr>
                <tr><th>SQLite-Version</th><td><?php echo esc_html( $status['sqlite_version'] ?: '–' ); ?></td></tr>
                <tr><th>Schema</th><td><?php echo $status['schema_ok'] ? 'vollständig' : '<strong>unvollständig</strong> (fehlend: ' . esc_html( implode( ', ', $status['missing'] ) ) . ')'; ?></td></tr>
                <tr><th>Werke gesamt</th><td><?php echo $status['works'] !== null ? number_format_i18n( $status['works'] ) : '–'; ?></td></tr>
                <tr><th>Mit Neusatz / Aufnahme / Kommentar</th><td><?php echo esc_html( $counts['neusatz'] . ' / ' . $counts['aufnahme'] . ' / ' . $counts['kommentar'] ); ?></td></tr>
                <tr><th>Werke ohne Dateien</th><td><?php echo esc_html( $counts['ohne_dateien'] ); ?></td></tr>
            </tbody>
        </table>

        <div class="evogt-tool-actions">
            <form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
                <?php wp_nonce_field( 'evogt_download_db' ); ?>
                <input type="hidden" name="action" value="evogt_download_db">
                <?php submit_button( 'Datenbank sichern (archive.db herunterladen)', 'primary', 'submit', false, $status['exists'] ? array() : array( 'disabled' => 'disabled' ) ); ?>
                <p class="description">Lädt einen konsistenten Schnappschuss der aktuellen Datenbank herunter. Diese Datei kann als <code>data/archive.db</code> ins Repository übernommen werden.</p>
            </form>

            <form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
                <?php wp_nonce_field( 'evogt_run_schema_migration' ); ?>
                <input type="hidden" name="action" value="evogt_run_schema_migration">
                <?php submit_button( 'Schema prüfen / migrieren', 'secondary', 'submit', false ); ?>
                <p class="description">Legt fehlende Spalten an (vorher wird automatisch eine Sicherungskopie neben der Datenbank erstellt).</p>
            </form>
        </div>

        <h2>Medien aus der Mediathek übernehmen</h2>
        <p>Früher wurden Neusatz-PDFs und Aufnahmen über die Kurzbeschreibung (Dateiname der Originaldatei) zugeordnet. Diese Zuordnung kann hier in die neuen Felder übernommen werden. Es werden nur leere Felder gefüllt; manuell gesetzte Dateien bleiben unverändert.</p>
        <?php if ( is_array( $migrated ) ) : ?>
            <p>Letzte Übernahme: <strong><?php echo esc_html( $migrated['at'] ); ?></strong> – übernommen: <?php echo (int) $migrated['migrated']; ?>, übersprungen: <?php echo (int) $migrated['skipped']; ?> (Anhänge mit Kurzbeschreibung: <?php echo (int) $migrated['total']; ?>).</p>
        <?php else : ?>
            <p>Noch nicht ausgeführt.</p>
        <?php endif; ?>
        <form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
            <?php wp_nonce_field( 'evogt_rerun_media_migration' ); ?>
            <input type="hidden" name="action" value="evogt_rerun_media_migration">
            <?php submit_button( 'Medien erneut übernehmen', 'secondary', 'submit', false, $status['schema_ok'] ? array() : array( 'disabled' => 'disabled' ) ); ?>
        </form>
        <?php if ( $log ) : ?>
            <details class="evogt-log">
                <summary>Protokoll der letzten Übernahme (<?php echo count( $log ); ?> Einträge)</summary>
                <pre><?php echo esc_html( implode( "\n", $log ) ); ?></pre>
            </details>
        <?php endif; ?>

        <h2>Sicherungskopien</h2>
        <?php if ( $backups ) : ?>
            <p>Automatische Kopien neben der Datenbank (die neuesten 10 werden behalten):</p>
            <ul class="evogt-file-list">
                <?php foreach ( $backups as $b ) : ?>
                    <li><code><?php echo esc_html( $b['name'] ); ?></code> <span class="evogt-muted"><?php echo esc_html( size_format( $b['size'], 1 ) . ' · ' . wp_date( 'd.m.Y H:i', $b['mtime'] ) ); ?></span></li>
                <?php endforeach; ?>
            </ul>
        <?php else : ?>
            <p class="evogt-muted">Noch keine Sicherungskopien vorhanden.</p>
        <?php endif; ?>
        <?php if ( ! $is_apache ) : ?>
            <p class="description">Hinweis: Dieser Server scheint kein Apache zu sein. Die mitgelieferte <code>.htaccess</code> greift dann nicht – bitte den Ordner <code><?php echo esc_html( dirname( $status['path'] ) ); ?></code> in der Serverkonfiguration (z. B. nginx <code>location</code>) gegen direkten Zugriff sperren.</p>
        <?php endif; ?>
    </div>
    <?php
}

/**
 * Stream a consistent snapshot of archive.db as a download.
 */
function evogt_handle_download_db() {
    if ( ! current_user_can( EVOGT_CAP ) ) wp_die( 'Keine Berechtigung.', 403 );
    check_admin_referer( 'evogt_download_db' );

    $db = evogt_get_db();
    if ( ! $db ) wp_die( 'Datenbank nicht gefunden.' );

    $tmp = EVOGT_DB_PATH . '.download-tmp';
    @unlink( $tmp );

    $ok = false;
    try {
        $db->exec( 'VACUUM INTO ' . $db->quote( $tmp ) ); // SQLite >= 3.27
        $ok = file_exists( $tmp );
    } catch ( PDOException $e ) {
        $ok = false;
    }
    if ( ! $ok ) {
        $ok = copy( EVOGT_DB_PATH, $tmp );
    }
    if ( ! $ok ) wp_die( 'Schnappschuss konnte nicht erstellt werden (Verzeichnis beschreibbar?).' );

    nocache_headers();
    header( 'Content-Type: application/octet-stream' );
    header( 'Content-Disposition: attachment; filename="archive-' . gmdate( 'Ymd-Hi' ) . '.db"' );
    header( 'Content-Length: ' . filesize( $tmp ) );
    readfile( $tmp );
    @unlink( $tmp );
    exit;
}

function evogt_handle_rerun_media_migration() {
    if ( ! current_user_can( EVOGT_CAP ) ) wp_die( 'Keine Berechtigung.', 403 );
    check_admin_referer( 'evogt_rerun_media_migration' );

    $result = evogt_migrate_caption_media( true );
    if ( is_wp_error( $result ) ) {
        set_transient( 'evogt_admin_flash', array( 'type' => 'error', 'msg' => $result->get_error_message() ), MINUTE_IN_SECONDS );
    } else {
        set_transient( 'evogt_admin_flash', array( 'type' => 'success', 'msg' => sprintf( 'Medien übernommen: %d, übersprungen: %d.', $result['migrated'], $result['skipped'] ) ), MINUTE_IN_SECONDS );
    }
    wp_safe_redirect( evogt_tools_url() );
    exit;
}

function evogt_handle_run_schema_migration() {
    if ( ! current_user_can( EVOGT_CAP ) ) wp_die( 'Keine Berechtigung.', 403 );
    check_admin_referer( 'evogt_run_schema_migration' );

    $result = evogt_schema_migrate();
    if ( is_wp_error( $result ) ) {
        set_transient( 'evogt_admin_flash', array( 'type' => 'error', 'msg' => $result->get_error_message() ), MINUTE_IN_SECONDS );
    } elseif ( $result['added'] ) {
        set_transient( 'evogt_admin_flash', array( 'type' => 'success', 'msg' => 'Spalten angelegt: ' . implode( ', ', $result['added'] ) . '. Sicherung: ' . basename( $result['backup'] ) ), MINUTE_IN_SECONDS );
    } else {
        set_transient( 'evogt_admin_flash', array( 'type' => 'success', 'msg' => 'Das Schema ist bereits vollständig.' ), MINUTE_IN_SECONDS );
    }
    delete_transient( 'evogt_schema_checked' );
    wp_safe_redirect( evogt_tools_url() );
    exit;
}
