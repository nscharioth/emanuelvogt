<?php
/**
 * Admin menu, assets, notices and the list page.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

require_once EVOGT_PLUGIN_DIR . 'includes/class-evogt-works-list-table.php';

add_action( 'admin_menu', 'evogt_admin_menu' );
add_action( 'admin_enqueue_scripts', 'evogt_admin_assets' );
add_action( 'admin_notices', 'evogt_admin_notices' );

function evogt_admin_menu() {
    add_menu_page( 'Werkverzeichnis', 'Werkverzeichnis', EVOGT_CAP, 'evogt-works', 'evogt_render_works_page', 'dashicons-playlist-audio', 26 );
    add_submenu_page( 'evogt-works', 'Alle Werke', 'Alle Werke', EVOGT_CAP, 'evogt-works', 'evogt_render_works_page' );
    add_submenu_page( 'evogt-works', 'Werkzeuge', 'Werkzeuge', EVOGT_CAP, 'evogt-tools', 'evogt_render_tools_page' );
}

function evogt_is_plugin_screen( $hook_suffix ) {
    return in_array( $hook_suffix, array( 'toplevel_page_evogt-works', 'werkverzeichnis_page_evogt-tools' ), true );
}

function evogt_admin_assets( $hook_suffix ) {
    if ( ! evogt_is_plugin_screen( $hook_suffix ) ) return;

    wp_enqueue_style( 'evogt-admin', EVOGT_PLUGIN_URL . 'assets/admin.css', array(), EVOGT_PLUGIN_VERSION );

    if ( $hook_suffix === 'toplevel_page_evogt-works' && isset( $_GET['action'] ) && $_GET['action'] === 'edit' ) {
        wp_enqueue_media();
        wp_enqueue_script( 'evogt-admin', EVOGT_PLUGIN_URL . 'assets/admin.js', array( 'jquery' ), EVOGT_PLUGIN_VERSION, true );
    }
}

/**
 * Notices: DB problems on every admin page (for users who can edit works),
 * flash messages and save results on the plugin's own pages.
 */
function evogt_admin_notices() {
    if ( ! current_user_can( EVOGT_CAP ) ) return;

    $screen    = get_current_screen();
    $on_plugin = $screen && evogt_is_plugin_screen( $screen->id );
    $status    = evogt_db_status();

    if ( ! $status['pdo_sqlite'] ) {
        echo '<div class="notice notice-error"><p><strong>Werkverzeichnis:</strong> Die PHP-Erweiterung <code>pdo_sqlite</code> fehlt. Werke können nicht gelesen werden.</p></div>';
    } elseif ( ! $status['exists'] ) {
        echo '<div class="notice notice-error"><p><strong>Werkverzeichnis:</strong> Die Datenbank wurde nicht gefunden: <code>' . esc_html( $status['path'] ) . '</code></p></div>';
    } elseif ( $on_plugin && ( ! $status['writable'] || ! $status['dir_writable'] ) ) {
        echo '<div class="notice notice-warning"><p><strong>Werkverzeichnis:</strong> Datenbank oder Datenverzeichnis sind nicht beschreibbar (<code>' . esc_html( dirname( $status['path'] ) ) . '</code>). Änderungen und Sicherungen sind nicht möglich.</p></div>';
    } elseif ( $on_plugin && ! $status['schema_ok'] ) {
        echo '<div class="notice notice-warning"><p><strong>Werkverzeichnis:</strong> Das Datenbank-Schema ist unvollständig (fehlend: ' . esc_html( implode( ', ', $status['missing'] ) ) . '). Bitte unter „Werkzeuge“ die Migration ausführen.</p></div>';
    }

    $flash = get_transient( 'evogt_admin_flash' );
    if ( $flash && is_array( $flash ) ) {
        delete_transient( 'evogt_admin_flash' );
        $type = $flash['type'] === 'error' ? 'notice-error' : ( $flash['type'] === 'warning' ? 'notice-warning' : 'notice-success' );
        echo '<div class="notice ' . $type . ' is-dismissible"><p>' . esc_html( $flash['msg'] ) . '</p></div>';
    }

    if ( ! $on_plugin ) return;

    if ( ! empty( $_GET['updated'] ) ) {
        echo '<div class="notice notice-success is-dismissible"><p>Werk gespeichert.</p></div>';
    }
    if ( ! empty( $_GET['evogt_error'] ) ) {
        $messages = array(
            'title'      => 'Der Titel darf nicht leer sein.',
            'attachment' => 'Ein ausgewählter Anhang ist ungültig (Neusatz muss ein PDF, Aufnahme eine Audiodatei sein).',
            'db'         => 'Die Änderung konnte nicht in der Datenbank gespeichert werden.',
            'notfound'   => 'Das Werk wurde nicht gefunden.',
        );
        $code = sanitize_key( $_GET['evogt_error'] );
        $msg  = isset( $messages[ $code ] ) ? $messages[ $code ] : 'Unbekannter Fehler.';
        if ( $code === 'attachment' && ! empty( $_GET['evogt_detail'] ) ) {
            $msg .= ' ' . sanitize_text_field( wp_unslash( $_GET['evogt_detail'] ) );
        }
        echo '<div class="notice notice-error is-dismissible"><p>' . esc_html( $msg ) . '</p></div>';
    }
}

/**
 * ?page=evogt-works[&action=edit&id=N]
 */
function evogt_render_works_page() {
    if ( ! current_user_can( EVOGT_CAP ) ) wp_die( 'Keine Berechtigung.', 403 );

    if ( isset( $_GET['action'] ) && $_GET['action'] === 'edit' ) {
        evogt_render_edit_page( isset( $_GET['id'] ) ? absint( $_GET['id'] ) : 0 );
        return;
    }
    evogt_render_list_page();
}

function evogt_render_list_page() {
    $table = new EVOGT_Works_List_Table();
    $table->prepare_items();
    ?>
    <div class="wrap evogt-wrap">
        <h1 class="wp-heading-inline">Werkverzeichnis</h1>
        <hr class="wp-header-end">
        <p class="description">Alle Werke aus <code>archive.db</code>. Suche nach Werknummer, Titel, Gattung, Besetzung oder Kommentar.</p>
        <form method="get">
            <input type="hidden" name="page" value="evogt-works">
            <?php if ( $table->current_filter() !== 'all' ) : ?>
                <input type="hidden" name="filter" value="<?php echo esc_attr( $table->current_filter() ); ?>">
            <?php endif; ?>
            <?php $table->views(); ?>
            <?php $table->search_box( 'Werke durchsuchen', 'evogt' ); ?>
            <?php $table->display(); ?>
        </form>
    </div>
    <?php
}
