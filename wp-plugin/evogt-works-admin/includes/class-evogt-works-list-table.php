<?php
/**
 * Admin list of all works with search, views, sorting and pagination.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

if ( ! class_exists( 'WP_List_Table' ) ) {
    require_once ABSPATH . 'wp-admin/includes/class-wp-list-table.php';
}

class EVOGT_Works_List_Table extends WP_List_Table {

    const PER_PAGE = 50;

    public function __construct() {
        parent::__construct( array(
            'singular' => 'werk',
            'plural'   => 'werke',
            'ajax'     => false,
        ) );
    }

    public function get_columns() {
        return array(
            'work_number'     => 'Nr.',
            'title'           => 'Titel',
            'genre'           => 'Gattung',
            'instrumentation' => 'Besetzung',
            'originals'       => 'Originale',
            'transcription'   => 'Neusatz',
            'audio'           => 'Aufnahme',
            'comment'         => 'Kommentar',
        );
    }

    public function get_sortable_columns() {
        return array(
            'work_number' => array( 'work_number', true ),
            'title'       => array( 'title', false ),
        );
    }

    protected function get_views() {
        $current = $this->current_filter();
        $search  = $this->current_search();
        $views   = array(
            'all'          => 'Alle',
            'neusatz'      => 'Mit Neusatz',
            'aufnahme'     => 'Mit Aufnahme',
            'kommentar'    => 'Mit Kommentar',
            'ohne_dateien' => 'Ohne Dateien',
        );

        $out = array();
        foreach ( $views as $key => $label ) {
            $count = evogt_works_count( array( 'filter' => $key, 's' => $search ) );
            $url   = add_query_arg( array( 'page' => 'evogt-works', 'filter' => $key, 's' => $search !== '' ? $search : null ), admin_url( 'admin.php' ) );
            $out[ $key ] = sprintf(
                '<a href="%s"%s>%s <span class="count">(%s)</span></a>',
                esc_url( $url ),
                $current === $key ? ' class="current" aria-current="page"' : '',
                esc_html( $label ),
                number_format_i18n( $count )
            );
        }
        return $out;
    }

    public function current_filter() {
        $filter = isset( $_REQUEST['filter'] ) ? sanitize_key( $_REQUEST['filter'] ) : 'all';
        return in_array( $filter, array( 'all', 'neusatz', 'aufnahme', 'kommentar', 'ohne_dateien' ), true ) ? $filter : 'all';
    }

    public function current_search() {
        return isset( $_REQUEST['s'] ) ? sanitize_text_field( wp_unslash( $_REQUEST['s'] ) ) : '';
    }

    public function prepare_items() {
        $this->_column_headers = array( $this->get_columns(), array(), $this->get_sortable_columns(), 'title' );

        $orderby = isset( $_REQUEST['orderby'] ) && $_REQUEST['orderby'] === 'title' ? 'title' : 'work_number';
        $order   = isset( $_REQUEST['order'] ) && strtolower( $_REQUEST['order'] ) === 'desc' ? 'desc' : 'asc';
        $paged   = $this->get_pagenum();

        $args = array(
            's'        => $this->current_search(),
            'filter'   => $this->current_filter(),
            'orderby'  => $orderby,
            'order'    => $order,
            'per_page' => self::PER_PAGE,
            'offset'   => ( $paged - 1 ) * self::PER_PAGE,
        );

        $total       = evogt_works_count( $args );
        $this->items = evogt_works_list( $args );

        $this->set_pagination_args( array(
            'total_items' => $total,
            'per_page'    => self::PER_PAGE,
            'total_pages' => (int) ceil( $total / self::PER_PAGE ),
        ) );
    }

    public function no_items() {
        echo 'Keine Werke gefunden.';
    }

    public static function edit_url( $id ) {
        return add_query_arg( array( 'page' => 'evogt-works', 'action' => 'edit', 'id' => (int) $id ), admin_url( 'admin.php' ) );
    }

    public function column_work_number( $item ) {
        return '<strong>' . esc_html( $item['work_number'] ) . '</strong>';
    }

    public function column_title( $item ) {
        $url   = self::edit_url( $item['id'] );
        $title = $item['title'] !== '' && $item['title'] !== null ? $item['title'] : '(ohne Titel)';
        $html  = sprintf( '<a class="row-title" href="%s">%s</a>', esc_url( $url ), esc_html( $title ) );
        $html .= '<div class="evogt-row-id">ID ' . (int) $item['id'] . '</div>';
        return $html . $this->row_actions( array(
            'edit' => sprintf( '<a href="%s">Bearbeiten</a>', esc_url( $url ) ),
        ) );
    }

    public function column_originals( $item ) {
        $n = (int) $item['file_count'];
        return $n ? number_format_i18n( $n ) : '<span class="evogt-muted">0</span>';
    }

    public function column_transcription( $item ) {
        return $this->check( ! empty( $item['transcription_attachment_id'] ) );
    }

    public function column_audio( $item ) {
        return $this->check( ! empty( $item['audio_attachment_id'] ) );
    }

    public function column_comment( $item ) {
        return $this->check( ! empty( $item['has_comment'] ) );
    }

    public function column_default( $item, $column_name ) {
        return isset( $item[ $column_name ] ) ? esc_html( $item[ $column_name ] ) : '';
    }

    private function check( $yes ) {
        return $yes
            ? '<span class="dashicons dashicons-yes evogt-yes" aria-label="ja"></span>'
            : '<span class="evogt-muted" aria-label="nein">&ndash;</span>';
    }
}
