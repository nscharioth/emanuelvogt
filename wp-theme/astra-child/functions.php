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
        wp_enqueue_style( 'evogt-app', get_stylesheet_directory_uri() . '/style.css', array('astra-parent-style'), '1.4.0' );
    
    // Only load the archive application logic on the front page
    if ( is_front_page() || is_page_template('front-page.php') ) {
        wp_enqueue_script( 'evogt-app-js', get_stylesheet_directory_uri() . '/assets/js/app.js', array(), '1.4.0', true );
        wp_localize_script( 'evogt-app-js', 'evogtSettings', array(
            'apiUrl'     => rest_url( 'evogt/v1' ),
            'pdfBaseUrl' => EVOGT_PDF_URL,
            'nonce'      => wp_create_nonce( 'wp_rest' )
        ) );
    }
}
add_action( 'wp_enqueue_scripts', 'astra_child_enqueue_styles' );

// -------------------------------------------------------
// Navigation: canonical menu + three layers of defence
// so the correct links always appear in the mobile menu.
// -------------------------------------------------------

/**
 * Return the ID of our "EV Hauptnavigation" WP menu,
 * creating it on first run if it does not yet exist.
 */
function evogt_get_canonical_menu_id() {
    $menu = wp_get_nav_menu_object( 'EV Hauptnavigation' );
    if ( $menu ) return (int) $menu->term_id;

    $id = wp_create_nav_menu( 'EV Hauptnavigation' );
    if ( is_wp_error( $id ) ) return null;

    wp_update_nav_menu_item( $id, 0, [
        'menu-item-title'  => 'Digitales Werkverzeichnis',
        'menu-item-url'    => home_url( '/' ),
        'menu-item-status' => 'publish',
        'menu-item-type'   => 'custom',
    ] );

    return (int) $id;
}

// Layer 1 — intercept wp_nav_menu() ARGS before rendering.
// Astra's Header Builder registers locations as ast_hf_menu_1, ast_hf_menu_2, etc.
// Redirect every one of them to our correct menu.
add_filter( 'wp_nav_menu_args', function( $args ) {
    if ( empty( $args['theme_location'] ) ) return $args;
    if ( strpos( $args['theme_location'], 'ast_hf_menu' ) === false ) return $args;

    $id = evogt_get_canonical_menu_id();
    if ( $id ) $args['menu'] = $id;
    return $args;
} );

// Layer 2 — intercept rendered HTML OUTPUT.
// Catches any menu that slipped past Layer 1 (e.g. Builder widget
// that passes a menu object directly instead of a theme_location).
add_filter( 'wp_nav_menu', function( $html, $args ) {
    if ( is_admin() ) return $html;
    $wrong = [ 'Dienstleistungen', 'Rezensionen', 'Warum wir' ];
    $found = false;
    foreach ( $wrong as $w ) {
        if ( strpos( $html, $w ) !== false ) { $found = true; break; }
    }
    if ( ! $found ) return $html;

    $active = is_front_page() ? ' current-menu-item' : '';
    return '<nav class="evogt-nav"><ul class="menu ast-menu-list">' .
        '<li class="menu-item' . $active . '"><a href="' . esc_url( home_url( '/' ) ) . '">Digitales Werkverzeichnis</a></li>' .
        '</ul></nav>';
}, 10, 2 );

// Desktop primary menu: prepend home link if absent
add_filter( 'wp_nav_menu_items', function( $items, $args ) {
    if ( empty( $args->theme_location ) || $args->theme_location !== 'primary' ) return $items;
    if ( strpos( $items, esc_url( home_url( '/' ) ) ) !== false ) return $items;

    $active = is_front_page() ? ' current-menu-item' : '';
    return '<li class="menu-item' . $active . '"><a href="' . esc_url( home_url( '/' ) ) . '">Digitales Werkverzeichnis</a></li>' . $items;
}, 10, 2 );

// Layer 3 — JS MutationObserver safety net (all pages, no PHP dependency).
// Fires on DOM-ready AND watches for Astra dynamically rendering the popup.
add_action( 'wp_footer', function () {
    $home_url = json_encode( home_url( '/' ) );
    ?>
<script>
(function () {
    var HOME  = <?php echo $home_url; ?>;
    var ITEM  = '<li class="menu-item"><a href="' + HOME + '">Digitales Werkverzeichnis</a></li>';
    var WRONG = ['Dienstleistungen', 'Rezensionen', 'Warum wir'];
    var SELS  = ['.ast-mobile-popup-inner', '#ast-mobile-popup', '.ast-fly-menu-wrap', '.ast-popup-full-overlay .ast-builder-menu'];

    function fix() {
        SELS.forEach(function (s) {
            document.querySelectorAll(s).forEach(function (el) {
                var ul = el.querySelector('ul');
                if (!ul) return;
                if (!WRONG.some(function (w) { return ul.textContent.indexOf(w) !== -1; })) return;
                ul.innerHTML = ITEM;
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        fix();
        new MutationObserver(fix).observe(document.body, { childList: true, subtree: true });
    });
})();
</script>
    <?php
}, 20 );

// Forcefully inject our custom title block directly into Astra's Header everywhere
// We use astra_site_identity to let it sit natively inside the flex layout
add_action('astra_site_identity', function() {
    echo '<div class="evogt-custom-brand-wrap" style="display: flex; align-items: center; gap: 1rem; margin-right: 2rem;">
            <a href="/" style="display:flex; flex-direction:column; text-decoration:none !important;">
                <span id="evogt-site-title" style="color: #d4af37 !important; font-family: Outfit, sans-serif !important; font-weight: 700 !important; font-size: 2.2rem !important; line-height: 1.1 !important; text-transform: uppercase !important; letter-spacing: 0.5px;">EMANUEL VOGT</span>
                <span id="evogt-site-subtitle" style="font-size: 0.95rem; font-family: Outfit, sans-serif !important; color: #a8a8a8 !important; text-transform: none; letter-spacing: 0.5px; margin-top: 4px;">Digitales Werkverzeichnis</span>
            </a>
            <img src="https://emanuel-vogt.info/wp-content/uploads/2026/07/emanuel-vogt-portrait-copyright-johannes-vogt-krause.jpg" alt="Emanuel Vogt" style="height: 68px; width: auto; border-radius: 50%; object-fit: cover; flex-shrink: 0;">
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
