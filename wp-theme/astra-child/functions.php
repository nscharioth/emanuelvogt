<?php
/**
 * Astra Child Theme functions and definitions
 */

// The archive data (SQLite) and the REST API evogt/v1 are provided by the plugin
// "EmanuelVogt Werkverzeichnis". The theme only needs the public URL of the scans.
if ( ! defined( 'EVOGT_PDF_URL' ) ) {
    define( 'EVOGT_PDF_URL', content_url() . '/uploads/archive/flat/' );
}

function astra_child_enqueue_styles() {
    // Parent theme style
    wp_enqueue_style( 'astra-parent-style', get_template_directory_uri() . '/style.css' );
    
    // Google Fonts
    wp_enqueue_style( 'evogt-fonts', 'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap', array(), null );
    
    // Child theme style
        wp_enqueue_style( 'evogt-app', get_stylesheet_directory_uri() . '/style.css', array('astra-parent-style'), '1.7.1' );
    
    // Only load the archive application logic on the front page
    if ( is_front_page() || is_page_template('front-page.php') ) {
        wp_enqueue_script( 'evogt-app-js', get_stylesheet_directory_uri() . '/assets/js/app.js', array(), '1.7.1', true );
        wp_localize_script( 'evogt-app-js', 'evogtSettings', array(
            'apiUrl'     => rest_url( 'evogt/v1' ),
            'pdfBaseUrl' => EVOGT_PDF_URL,
            'nonce'      => wp_create_nonce( 'wp_rest' )
        ) );
    }
}
add_action( 'wp_enqueue_scripts', 'astra_child_enqueue_styles' );

// -------------------------------------------------------
// Navigation: keep desktop and mobile on the same WP menu.
// -------------------------------------------------------

/**
 * Resolve the menu assigned to the desktop header first,
 * so the mobile drawer can reuse the same menu source.
 */
function evogt_get_canonical_menu_id() {
    $locations = get_nav_menu_locations();
    $preferred_locations = [ 'primary', 'ast_hf_menu_1', 'ast_hf_menu_2' ];

    foreach ( $preferred_locations as $location ) {
        if ( ! empty( $locations[ $location ] ) ) {
            return (int) $locations[ $location ];
        }
    }

    foreach ( $locations as $location => $menu_id ) {
        if ( empty( $menu_id ) ) continue;
        if ( strpos( $location, 'ast_hf_menu' ) !== false ) {
            return (int) $menu_id;
        }
    }

    $menu = wp_get_nav_menu_object( 'EV Hauptnavigation' );
    return $menu ? (int) $menu->term_id : null;
}

function evogt_get_mobile_menu_items() {
    $current_page_id = get_queried_object_id();
    $items = [
        [ 'title' => 'Über Emanuel Vogt', 'slug' => 'ueber-emanuel-vogt' ],
        [ 'title' => 'Das Projekt „EVV – Emanuel-Vogt-Verzeichnis“', 'slug' => 'das-projekt' ],
        [ 'title' => 'Über das Werkverzeichnis', 'slug' => 'ueber-das-werkverzeichnis' ],
        [ 'title' => 'Kontakt', 'slug' => 'kontakt' ],
        [ 'title' => 'Datenschutzerklärung', 'slug' => 'datenschutzerklaerung' ],
        [ 'title' => 'Impressum', 'slug' => 'impressum' ],
    ];

    foreach ( $items as &$item ) {
        $page = get_page_by_path( $item['slug'] );
        $item['page_id'] = $page ? (int) $page->ID : 0;
        $item['url'] = $page ? get_permalink( $page ) : home_url( '/' . $item['slug'] . '/' );
        $item['active'] = $item['page_id'] && $item['page_id'] === $current_page_id;
    }

    return $items;
}

function evogt_render_forced_mobile_menu( $ul_attributes = '' ) {
    $items = evogt_get_mobile_menu_items();
    $html = '<ul ' . trim( $ul_attributes ) . '>';

    foreach ( $items as $item ) {
        $classes = 'menu-item menu-item-type-post_type menu-item-object-page';
        if ( ! empty( $item['active'] ) ) {
            $classes .= ' current-menu-item';
        }

        $rel = $item['title'] === 'Datenschutzerklärung' ? ' rel="privacy-policy"' : '';
        $html .= '<li class="' . esc_attr( $classes ) . '"><a href="' . esc_url( $item['url'] ) . '" class="menu-link"' . $rel . '>' . esc_html( $item['title'] ) . '</a></li>';
    }

    $html .= '</ul>';
    return $html;
}

// Mirror the desktop menu assignment into Astra's mobile header locations.
add_filter( 'wp_nav_menu_args', function( $args ) {
    if ( empty( $args['theme_location'] ) ) return $args;
    if ( strpos( $args['theme_location'], 'ast_hf_menu' ) === false ) return $args;

    $id = evogt_get_canonical_menu_id();
    if ( $id ) $args['menu'] = $id;
    return $args;
} );

// Keep the home link consistent in the desktop header menu.
add_filter( 'wp_nav_menu_items', function( $items, $args ) {
    $theme_location = $args->theme_location ?? '';
    if ( $theme_location !== 'primary' && $theme_location !== 'ast_hf_menu_1' ) {
        return $items;
    }
    if ( strpos( $items, esc_url( home_url( '/' ) ) ) !== false ) return $items;

    $active = is_front_page() ? ' current-menu-item' : '';
    return '<li class="menu-item' . $active . '"><a href="' . esc_url( home_url( '/' ) ) . '">Digitales Werkverzeichnis</a></li>' . $items;
}, 10, 2 );

add_filter( 'wp_nav_menu', function( $html, $args ) {
    if ( is_admin() ) return $html;

    $is_mobile_menu = strpos( $html, 'id="ast-hf-mobile-menu"' ) !== false
        || strpos( $html, 'ast-mobile-site-navigation' ) !== false
        || strpos( $html, 'Website-Navigation: Hauptmenü (2)' ) !== false;

    if ( ! $is_mobile_menu ) {
        return $html;
    }

    if ( preg_match( '/<ul([^>]*)>.*<\/ul>/si', $html, $matches ) ) {
        return preg_replace(
            '/<ul([^>]*)>.*<\/ul>/si',
            evogt_render_forced_mobile_menu( trim( $matches[1] ) ),
            $html,
            1
        );
    }

    return $html;
}, 20, 2 );

// Forcefully inject our custom title block directly into Astra's Header everywhere
// We use astra_site_identity to let it sit natively inside the flex layout
add_action('astra_site_identity', function() {
    echo '<div class="evogt-custom-brand-wrap" style="display: flex; align-items: center; gap: 1rem; margin-right: 2rem;">
            <a href="/" style="display:flex; flex-direction:column; text-decoration:none !important;">
                <span id="evogt-site-title" style="color: #d4af37 !important; font-family: Outfit, sans-serif !important; font-weight: 700 !important; font-size: 2.2rem !important; line-height: 1.1 !important; text-transform: uppercase !important; letter-spacing: 0.5px;">EMANUEL VOGT</span>
                <span id="evogt-site-subtitle" style="font-size: 0.95rem; font-family: Outfit, sans-serif !important; color: #a8a8a8 !important; text-transform: none; letter-spacing: 0.5px; margin-top: 4px;">Digitales Werkverzeichnis</span>
            </a>
            <img src="https://emanuel-vogt.info/wp-content/uploads/2026/08/emanuel-vogt-portrait-copyright-johannes-vogt-krause-v3.jpg" alt="Emanuel Vogt" style="height: 85px; width: 85px; border-radius: 0; object-fit: cover; flex-shrink: 0;">
          </div>';
}, 1);

// Everything data-related (SQLite access, REST API evogt/v1, media links) lives in the
// plugin "EmanuelVogt Werkverzeichnis" (wp-plugin/evogt-works-admin). Warn if it is missing.
add_action( 'admin_notices', function() {
    if ( function_exists( 'evogt_get_db' ) || ! current_user_can( 'activate_plugins' ) ) return;
    echo '<div class="notice notice-error"><p><strong>Astra Child für Emanuel Vogt:</strong> Das Plugin „EmanuelVogt Werkverzeichnis“ ist nicht aktiv – Suche und Werkanzeige auf der Startseite funktionieren nicht.</p></div>';
} );
