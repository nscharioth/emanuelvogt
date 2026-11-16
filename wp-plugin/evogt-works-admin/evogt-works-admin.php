<?php
/**
 * Plugin Name: EmanuelVogt Werkverzeichnis
 * Description: Verwaltung der Werke des Emanuel-Vogt-Archivs (SQLite archive.db): Titel, Neusatz-PDF, Aufnahme, Kommentar. Stellt die REST-API evogt/v1 für das Theme bereit.
 * Version: 1.1.0
 * Requires PHP: 7.4
 * Author: Emanuel-Vogt-Archiv
 * Text Domain: evogt
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'EVOGT_PLUGIN_VERSION', '1.1.0' );
define( 'EVOGT_PLUGIN_FILE', __FILE__ );
define( 'EVOGT_PLUGIN_DIR', plugin_dir_path( __FILE__ ) );
define( 'EVOGT_PLUGIN_URL', plugin_dir_url( __FILE__ ) );

// Capability required for the admin area and the writing REST endpoints
// (matches the PDF-rotation control that already existed in the theme).
if ( ! defined( 'EVOGT_CAP' ) ) define( 'EVOGT_CAP', 'edit_posts' );

// Location of the SQLite archive and the flat folder with the scanned originals.
if ( ! defined( 'EVOGT_DB_PATH' ) ) define( 'EVOGT_DB_PATH', WP_CONTENT_DIR . '/uploads/archive/data/archive.db' );
if ( ! defined( 'EVOGT_PDF_URL' ) ) define( 'EVOGT_PDF_URL', content_url() . '/uploads/archive/flat/' );

require_once EVOGT_PLUGIN_DIR . 'includes/db.php';
require_once EVOGT_PLUGIN_DIR . 'includes/schema.php';
require_once EVOGT_PLUGIN_DIR . 'includes/media-migration.php';
require_once EVOGT_PLUGIN_DIR . 'includes/works-repo.php';
require_once EVOGT_PLUGIN_DIR . 'includes/rest.php';

if ( is_admin() ) {
    require_once EVOGT_PLUGIN_DIR . 'includes/admin.php';
    require_once EVOGT_PLUGIN_DIR . 'includes/admin-edit.php';
    require_once EVOGT_PLUGIN_DIR . 'includes/admin-tools.php';
}

add_action( 'rest_api_init', 'evogt_register_rest_routes' );
add_action( 'init', 'evogt_upgrade_schema_on_init', 5 );
add_action( 'admin_init', 'evogt_maybe_migrate_schema' );
add_action( 'delete_attachment', 'evogt_detach_attachment' );

register_activation_hook( __FILE__, 'evogt_activate' );

/**
 * Activation: migrate the SQLite schema (with backup), import caption-linked
 * media once, protect the data directory and clear caches.
 */
function evogt_activate() {
    evogt_write_htaccess_guard();

    $result = evogt_schema_migrate();
    if ( is_wp_error( $result ) ) {
        // Nothing fatal: the admin notice explains the problem (DB missing / not writable).
        set_transient( 'evogt_admin_flash', array( 'type' => 'error', 'msg' => $result->get_error_message() ), 5 * MINUTE_IN_SECONDS );
    } elseif ( ! get_option( 'evogt_media_migrated' ) ) {
        $m = evogt_migrate_caption_media();
        if ( ! is_wp_error( $m ) ) {
            set_transient( 'evogt_admin_flash', array(
                'type' => 'success',
                'msg'  => sprintf( 'Werkverzeichnis aktiviert. Medien aus der Mediathek übernommen: %d, übersprungen: %d.', $m['migrated'], $m['skipped'] ),
            ), 5 * MINUTE_IN_SECONDS );
        }
    }

    delete_transient( 'evogt_all_works' );
    delete_transient( 'evogt_recordings' );
    delete_transient( 'evogt_media_map' ); // left over from the theme-based implementation
}
