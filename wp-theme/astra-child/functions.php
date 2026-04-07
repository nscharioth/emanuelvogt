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
    wp_enqueue_style( 'evogt-app', get_stylesheet_directory_uri() . '/style.css', array('astra-parent-style'), '1.0.3' );
    
    // Only load the archive application logic on the front page
    if ( is_front_page() || is_page_template('front-page.php') ) {
        wp_enqueue_script( 'evogt-app-js', get_stylesheet_directory_uri() . '/assets/js/app.js', array(), '1.0.3', true );
        wp_localize_script( 'evogt-app-js', 'evogtSettings', array(
            'apiUrl' => rest_url( 'evogt/v1' ),
            'pdfBaseUrl' => EVOGT_PDF_URL
        ) );
    }
}
add_action( 'wp_enqueue_scripts', 'astra_child_enqueue_styles' );

// Forcefully inject our custom title block directly into Astra's Header everywhere
// We use astra_site_identity to let it sit natively inside the flex layout
add_action('astra_site_identity', function() {
    echo '<div class="evogt-custom-brand-wrap" style="display: flex; margin-right: 2rem;">
            <a href="/" style="display:flex; flex-direction:column; text-decoration:none !important;">
                <span id="evogt-site-title" style="color: #d4af37 !important; font-family: Outfit, sans-serif !important; font-weight: 700 !important; font-size: 2.2rem !important; line-height: 1.1 !important; text-transform: uppercase !important; letter-spacing: 0.5px;">EMANUEL VOGT</span>
                <span id="evogt-site-subtitle" style="font-size: 0.95rem; font-family: Outfit, sans-serif !important; color: #a8a8a8 !important; text-transform: none; letter-spacing: 0.5px; margin-top: 4px;">Digitales Werkverzeichnis (1925-2007)</span>
            </a>
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
    
    register_rest_route('evogt/v1', '/musicxml/list', array(
        'methods' => 'GET',
        'callback' => 'evogt_api_get_musicxml_list',
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

    $q = sanitize_text_field($request->get_param('q'));
    $genre = sanitize_text_field($request->get_param('genre') ?? 'All');
    $instrumentation = sanitize_text_field($request->get_param('instrumentation') ?? 'All');

    $query = "SELECT id, work_number, title, genre, instrumentation FROM works WHERE 1=1";
    $params = [];

    if ($genre !== 'All') {
        $query .= " AND genre = ?";
        $params[] = $genre;
    }
    if ($instrumentation !== 'All') {
        $query .= " AND (instrumentation LIKE ? OR instrumentation LIKE ? OR instrumentation LIKE ? OR instrumentation = ?)";
        $params[] = $instrumentation . ',%';
        $params[] = '%, ' . $instrumentation . ',%';
        $params[] = '%, ' . $instrumentation;
        $params[] = $instrumentation;
    }

    $stmt = $db->prepare($query);
    $stmt->execute($params);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $results = [];
    $search_term = $q ? mb_strtolower($q, 'UTF-8') : null;

    foreach ($rows as $r) {
        if ($search_term) {
            $t = mb_strtolower($r['title'] ?? '', 'UTF-8');
            $w = mb_strtolower($r['work_number'] ?? '', 'UTF-8');
            if (strpos($t, $search_term) === false && $w !== $search_term) {
                continue;
            }
        }
        $results[] = $r;
    }

    usort($results, 'natural_sort_logic');
    return new WP_REST_Response($results, 200);
}

function evogt_api_get_musicxml_list($request) {
    $upload_dir = wp_upload_dir();
    $musicxml_dir = $upload_dir['basedir'] . '/archive/musicxml/';
    
    if (!is_dir($musicxml_dir)) {
        return rest_ensure_response(array());
    }
    
    $files = array();
    $dir_contents = scandir($musicxml_dir);
    if ($dir_contents !== false) {
        foreach ($dir_contents as $file) {
            // Only process .xml or .musicxml files
            if (preg_match('/\.(xml|musicxml)$/i', $file)) {
                // Parse work ID (e.g. "461-sonata...xml" -> 461)
                preg_match('/^(\d+)/', $file, $matches);
                $work_id = isset($matches[1]) ? intval($matches[1]) : null;
                
                $files[] = array(
                    'filename' => $file,
                    'work_number' => $work_id,
                    'work_title' => $file, // Simplified
                    'url' => content_url() . '/uploads/archive/musicxml/' . rawurlencode($file)
                );
            }
        }
    }
    
    return rest_ensure_response($files);
}

function evogt_api_get_work($request) {
    $db = evogt_get_db();
    if (!$db) return new WP_REST_Response('Database not found', 500);

    $id = intval($request->get_param('id'));

    $stmt = $db->prepare("SELECT id, work_number, title, genre, instrumentation, has_musicxml FROM works WHERE id = ?");
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

    $work['has_musicxml'] = !empty($work['has_musicxml']) ? true : false;
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
