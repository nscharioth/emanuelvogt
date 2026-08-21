<?php
/**
 * Astra Child Theme functions and definitions
 */

// Define where the SQLite DB is placed. You can change this path later.
// Recommended location: wp-content/uploads/archive/data/archive.db
define( 'EVOGT_DB_PATH', WP_CONTENT_DIR . '/uploads/archive/data/archive.db' );
define( 'EVOGT_PDF_URL', content_url() . '/uploads/archive/flat/' );

function astra_child_enqueue_styles() {
    // Parent theme style
    wp_enqueue_style( 'astra-parent-style', get_template_directory_uri() . '/style.css' );
    
    // Google Fonts
    wp_enqueue_style( 'evogt-fonts', 'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap', array(), null );
    
    // Child theme style
        wp_enqueue_style( 'evogt-app', get_stylesheet_directory_uri() . '/style.css', array('astra-parent-style'), '1.5.0' );
    
    // Only load the archive application logic on the front page
    if ( is_front_page() || is_page_template('front-page.php') ) {
        wp_enqueue_script( 'evogt-app-js', get_stylesheet_directory_uri() . '/assets/js/app.js', array(), '1.5.0', true );
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
            <img src="https://emanuel-vogt.info/wp-content/uploads/2026/08/emanuel-vogt-portrait-copyright-johannes-vogt-krause-v2.jpg" alt="Emanuel Vogt" style="height: 85px; width: 85px; border-radius: 0; object-fit: cover; flex-shrink: 0;">
          </div>';
}, 1);

// REST API Endpoints
add_action('rest_api_init', function () {
    register_rest_route('evogt/v1', '/works', array(
        'methods' => 'GET',
        'callback' => 'evogt_api_get_works',
        'permission_callback' => '__return_true'
    ));

    register_rest_route('evogt/v1', '/work/(?P<id>\d+)', array(
        'methods' => 'GET',
        'callback' => 'evogt_api_get_work',
        'permission_callback' => '__return_true'
    ));

    register_rest_route('evogt/v1', '/genres', array(
        'methods' => 'GET',
        'callback' => 'evogt_api_get_genres',
        'permission_callback' => '__return_true'
    ));
    
    register_rest_route('evogt/v1', '/instrumentations', array(
        'methods' => 'GET',
        'callback' => 'evogt_api_get_instrumentations',
        'permission_callback' => '__return_true'
    ));

    // PDF Rotation Endpoints
    register_rest_route('evogt/v1', '/pdf-rotation/(?P<file_id>\d+)', array(
        'methods' => 'GET',
        'callback' => 'evogt_api_get_pdf_rotation',
        'permission_callback' => '__return_true'
    ));

    register_rest_route('evogt/v1', '/pdf-rotation/(?P<file_id>\d+)', array(
        'methods' => 'POST',
        'callback' => 'evogt_api_set_pdf_rotation',
        'permission_callback' => function () {
            // Only logged-in users with edit_posts capability can rotate PDFs
            return current_user_can('edit_posts');
        }
    ));
});

function evogt_get_db() {
    if (!file_exists(EVOGT_DB_PATH)) {
        return null; // DB file missing
    }
    $db = new PDO('sqlite:' . EVOGT_DB_PATH);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    return $db;
}

function natural_sort_logic($a, $b) {
    return strnatcasecmp($a['work_number'] ?? '', $b['work_number'] ?? '');
}

function evogt_api_get_works($request) {
    $db = evogt_get_db();
    if (!$db) return new WP_REST_Response('Database not found', 500);

    $q = sanitize_text_field( trim( $request->get_param('q') ?? '' ) );

    if ( $q === '' ) {
        // No search query — serve from transient cache (5-min TTL)
        $rows = get_transient( 'evogt_all_works' );
        if ( $rows === false ) {
            $stmt = $db->query("SELECT id, work_number, title, genre, instrumentation FROM works ORDER BY work_number");
            $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
            usort($rows, 'natural_sort_logic');
            set_transient( 'evogt_all_works', $rows, 5 * MINUTE_IN_SECONDS );
        }
    } else {
        // Search: let SQLite do the filtering with LIKE
        $like = '%' . $q . '%';
        $stmt = $db->prepare(
            "SELECT id, work_number, title, genre, instrumentation FROM works
             WHERE title LIKE ? OR work_number LIKE ? OR genre LIKE ? OR instrumentation LIKE ?"
        );
        $stmt->execute([$like, $like, $like, $like]);
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        usort($rows, 'natural_sort_logic');
    }

    $response = new WP_REST_Response($rows, 200);
    $response->header('Cache-Control', 'public, max-age=60');
    return $response;
}

function evogt_api_get_work($request) {
    $db = evogt_get_db();
    if (!$db) return new WP_REST_Response('Database not found', 500);

    $id = intval($request->get_param('id'));

    $stmt = $db->prepare("SELECT id, work_number, title, genre, instrumentation FROM works WHERE id = ?");
    $stmt->execute([$id]);
    $work = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$work) {
        return new WP_REST_Response('Not found', 404);
    }

    $stmt_files = $db->prepare("
        SELECT f.id, f.filename, f.file_type, f.size_bytes, f.flat_path,
               COALESCE(r.rotation, 0) as rotation
        FROM files f
        LEFT JOIN pdf_rotations r ON f.id = r.file_id
        WHERE f.work_id = ?
    ");
    $stmt_files->execute([$id]);
    $file_rows = $stmt_files->fetchAll(PDO::FETCH_ASSOC);

    $files = [];
    foreach ($file_rows as $f) {
        // If flat_path is present, use it, else fallback to filename
        $name_to_use = !empty($f['flat_path']) ? $f['flat_path'] : $f['filename'];
        $files[] = array(
            'id' => $f['id'],
            'filename' => $f['filename'],
            'url' => EVOGT_PDF_URL . rawurlencode(basename($name_to_use)),
            'type' => $f['file_type'],
            'size' => $f['size_bytes'],
            'rotation' => intval($f['rotation'])
        );
    }

    $work['files'] = $files;

    return new WP_REST_Response($work, 200);
}

function evogt_api_get_genres() {
    $db = evogt_get_db();
    if (!$db) return new WP_REST_Response('Database not found', 500);

    $stmt = $db->query("SELECT DISTINCT genre FROM works WHERE genre IS NOT NULL");
    $rows = $stmt->fetchAll(PDO::FETCH_COLUMN);

    $genres = ['All'];
    foreach ($rows as $r) {
        $genres[] = $r;
    }
    $filtered = array_unique($genres);
    return new WP_REST_Response(array_values($filtered), 200);
}

function evogt_api_get_instrumentations() {
    $db = evogt_get_db();
    if (!$db) return new WP_REST_Response('Database not found', 500);

    $stmt = $db->query("SELECT DISTINCT instrumentation FROM works WHERE instrumentation IS NOT NULL");
    $rows = $stmt->fetchAll(PDO::FETCH_COLUMN);

    $all_instruments = [];
    foreach ($rows as $inst) {
        if ($inst) {
            $parts = explode(',', $inst);
            foreach ($parts as $p) {
                $all_instruments[] = trim($p);
            }
        }
    }
    
    $unique = array_unique($all_instruments);
    sort($unique);
    array_unshift($unique, 'All');
    
    return new WP_REST_Response($unique, 200);
}

function evogt_api_get_pdf_rotation($request) {
    $db = evogt_get_db();
    if (!$db) return new WP_REST_Response('Database not found', 500);
    $file_id = intval($request->get_param('file_id'));
    
    $stmt = $db->prepare("SELECT rotation FROM pdf_rotations WHERE file_id = ?");
    $stmt->execute([$file_id]);
    $res = $stmt->fetchColumn();
    
    return new WP_REST_Response(['file_id' => $file_id, 'rotation' => $res !== false ? intval($res) : 0], 200);
}

function evogt_api_set_pdf_rotation($request) {
    if (!current_user_can('edit_posts')) {
        return new WP_REST_Response('Unauthorized', 403);
    }

    $db = evogt_get_db();
    if (!$db) return new WP_REST_Response('Database not found', 500);
    $file_id = intval($request->get_param('file_id'));
    $params = $request->get_json_params();
    $rotation = intval($params['rotation'] ?? 0);

    if (!in_array($rotation, [0, 90, 180, 270])) {
        return new WP_REST_Response('Invalid rotation', 400);
    }

    $stmt = $db->prepare("
        INSERT OR REPLACE INTO pdf_rotations (file_id, rotation, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    ");
    $stmt->execute([$file_id, $rotation]);

    return new WP_REST_Response(['file_id' => $file_id, 'rotation' => $rotation, 'saved' => true], 200);
}

// Clear the works transient whenever it might be stale (e.g. admin saves a post)
add_action( 'save_post', function() { delete_transient( 'evogt_all_works' ); } );
