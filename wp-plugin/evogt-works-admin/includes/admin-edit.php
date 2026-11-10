<?php
/**
 * Edit screen for a single work and its save handler.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

add_action( 'admin_post_evogt_save_work', 'evogt_handle_save_work' );

function evogt_render_edit_page( $id ) {
    $work = $id ? evogt_get_work( $id ) : null;
    $list_url = add_query_arg( array( 'page' => 'evogt-works' ), admin_url( 'admin.php' ) );

    if ( ! $work ) {
        echo '<div class="wrap evogt-wrap"><h1>Werk bearbeiten</h1><div class="notice notice-error"><p>Das Werk wurde nicht gefunden.</p></div>';
        echo '<p><a href="' . esc_url( $list_url ) . '">&larr; Zurück zur Liste</a></p></div>';
        return;
    }

    $return = wp_get_referer();
    if ( ! $return || strpos( $return, 'page=evogt-works' ) === false || strpos( $return, 'action=edit' ) !== false ) {
        $return = isset( $_GET['return'] ) ? esc_url_raw( wp_unslash( $_GET['return'] ) ) : $list_url;
    }
    $files = evogt_get_work_files( $id );
    ?>
    <div class="wrap evogt-wrap">
        <h1 class="wp-heading-inline">Werk bearbeiten</h1>
        <a href="<?php echo esc_url( $return ); ?>" class="page-title-action">&larr; Zurück zur Liste</a>
        <hr class="wp-header-end">

        <form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" class="evogt-edit-form">
            <?php wp_nonce_field( 'evogt_save_work_' . (int) $work['id'], '_evogt_nonce' ); ?>
            <input type="hidden" name="action" value="evogt_save_work">
            <input type="hidden" name="work_id" value="<?php echo (int) $work['id']; ?>">
            <input type="hidden" name="return" value="<?php echo esc_attr( $return ); ?>">

            <table class="form-table" role="presentation">
                <tr>
                    <th scope="row">ID</th>
                    <td>
                        <input type="text" value="<?php echo (int) $work['id']; ?>" class="small-text" readonly>
                        <span class="evogt-inline-label">Werknummer</span>
                        <input type="text" value="<?php echo esc_attr( $work['work_number'] ); ?>" class="small-text" readonly>
                        <p class="description">ID und Werknummer sind fest vergeben.
                            <?php if ( $work['genre'] || $work['instrumentation'] ) : ?>
                                Gattung: <strong><?php echo esc_html( $work['genre'] ?: '–' ); ?></strong>,
                                Besetzung: <strong><?php echo esc_html( $work['instrumentation'] ?: '–' ); ?></strong>
                            <?php endif; ?>
                        </p>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="evogt_title">Titel</label></th>
                    <td><input type="text" id="evogt_title" name="evogt_title" class="regular-text" required value="<?php echo esc_attr( $work['title'] ); ?>"></td>
                </tr>
                <tr>
                    <th scope="row">Originale (Scans)</th>
                    <td>
                        <?php if ( $files ) : ?>
                            <ul class="evogt-file-list">
                                <?php foreach ( $files as $f ) : ?>
                                    <li>
                                        <span class="dashicons <?php echo preg_match( '/^(jpg|jpeg|png)$/i', (string) $f['type'] ) ? 'dashicons-format-image' : 'dashicons-media-document'; ?>"></span>
                                        <a href="<?php echo esc_url( $f['url'] ); ?>" target="_blank" rel="noopener"><?php echo esc_html( $f['filename'] ); ?></a>
                                        <span class="evogt-muted">
                                            <?php echo $f['size'] ? esc_html( size_format( (int) $f['size'], 1 ) ) : '–'; ?>
                                            <?php if ( $f['rotation'] ) : ?> · Rotation <?php echo (int) $f['rotation']; ?>°<?php endif; ?>
                                        </span>
                                    </li>
                                <?php endforeach; ?>
                            </ul>
                        <?php else : ?>
                            <p class="evogt-muted">Keine Dateien im Archiv vorhanden.</p>
                        <?php endif; ?>
                        <p class="description">Die Originalscans werden über das Archiv-Verzeichnis verwaltet und können hier nur angesehen werden.</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Neusatz (PDF)</th>
                    <td>
                        <?php evogt_render_media_field( 'evogt_transcription_id', $work['transcription_attachment_id'], 'application/pdf', 'transcription' ); ?>
                        <p class="description">Neu gesetzte Partitur als PDF. Wird im Werk-Dialog als „Neusatz (PDF)“ angezeigt.</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Aufnahme (MP3)</th>
                    <td>
                        <?php evogt_render_media_field( 'evogt_audio_id', $work['audio_attachment_id'], 'audio', 'audio' ); ?>
                        <p class="description">Tonaufnahme des Werks. Erscheint im Werk-Dialog und auf der Startseite unter „Aufnahmen“.</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row"><label for="evogt_comment">Kommentar</label></th>
                    <td>
                        <textarea id="evogt_comment" name="evogt_comment" rows="8" class="large-text"><?php echo esc_textarea( (string) $work['comment'] ); ?></textarea>
                        <p class="description">Erscheint im Werk-Dialog auf der Website. Absätze werden automatisch gesetzt; einfache HTML-Tags (Links, Fett, Kursiv) sind erlaubt.</p>
                    </td>
                </tr>
            </table>

            <?php submit_button( 'Speichern' ); ?>
            <?php if ( ! empty( $work['updated_at'] ) ) : ?>
                <p class="evogt-muted">Zuletzt geändert: <?php echo esc_html( $work['updated_at'] ); ?> (UTC)</p>
            <?php endif; ?>
        </form>
    </div>
    <?php
}

/**
 * Media picker field: hidden id + preview + select/remove buttons.
 */
function evogt_render_media_field( $name, $attachment_id, $mime, $kind ) {
    $item = evogt_attachment_item( $attachment_id, $kind );
    $icon = $kind === 'audio' ? 'dashicons-format-audio' : 'dashicons-media-document';
    ?>
    <div class="evogt-media-field" data-mime="<?php echo esc_attr( $mime ); ?>" data-title="<?php echo $kind === 'audio' ? 'Aufnahme auswählen' : 'Neusatz-PDF auswählen'; ?>">
        <input type="hidden" name="<?php echo esc_attr( $name ); ?>" class="evogt-media-id" value="<?php echo $item ? (int) $item['attachment_id'] : 0; ?>">
        <p class="evogt-media-preview">
            <?php if ( $item ) : ?>
                <span class="dashicons <?php echo $icon; ?>"></span>
                <a href="<?php echo esc_url( $item['url'] ); ?>" target="_blank" rel="noopener"><?php echo esc_html( $item['title'] ?: basename( $item['url'] ) ); ?></a>
                <span class="evogt-muted">
                    <?php if ( $kind === 'audio' ) : ?><?php echo esc_html( $item['length_formatted'] ); ?><?php elseif ( ! empty( $item['size'] ) ) : ?><?php echo esc_html( size_format( $item['size'], 1 ) ); ?><?php endif; ?>
                    · Mediathek #<?php echo (int) $item['attachment_id']; ?>
                </span>
            <?php elseif ( $attachment_id ) : ?>
                <span class="evogt-muted">Der verknüpfte Anhang #<?php echo (int) $attachment_id; ?> existiert nicht mehr in der Mediathek.</span>
            <?php else : ?>
                <span class="evogt-muted">Keine Datei ausgewählt.</span>
            <?php endif; ?>
        </p>
        <button type="button" class="button evogt-media-select">Auswählen / Hochladen</button>
        <button type="button" class="button-link-delete evogt-media-remove" <?php echo $item ? '' : 'hidden'; ?>>Entfernen</button>
    </div>
    <?php
}

/**
 * admin-post.php?action=evogt_save_work
 */
function evogt_handle_save_work() {
    if ( ! current_user_can( EVOGT_CAP ) ) wp_die( 'Keine Berechtigung.', 403 );

    $id = isset( $_POST['work_id'] ) ? absint( $_POST['work_id'] ) : 0;
    check_admin_referer( 'evogt_save_work_' . $id, '_evogt_nonce' );

    $edit_url = add_query_arg( array( 'page' => 'evogt-works', 'action' => 'edit', 'id' => $id ), admin_url( 'admin.php' ) );
    if ( ! empty( $_POST['return'] ) ) {
        $edit_url = add_query_arg( 'return', rawurlencode( esc_url_raw( wp_unslash( $_POST['return'] ) ) ), $edit_url );
    }

    if ( ! $id || ! evogt_get_work( $id ) ) {
        wp_safe_redirect( add_query_arg( 'evogt_error', 'notfound', $edit_url ) );
        exit;
    }

    $title = isset( $_POST['evogt_title'] ) ? sanitize_text_field( wp_unslash( $_POST['evogt_title'] ) ) : '';
    if ( $title === '' ) {
        wp_safe_redirect( add_query_arg( 'evogt_error', 'title', $edit_url ) );
        exit;
    }

    $comment = isset( $_POST['evogt_comment'] ) ? trim( wp_kses_post( wp_unslash( $_POST['evogt_comment'] ) ) ) : '';

    $t_id = evogt_validate_attachment( isset( $_POST['evogt_transcription_id'] ) ? $_POST['evogt_transcription_id'] : 0, 'application/pdf' );
    $a_id = evogt_validate_attachment( isset( $_POST['evogt_audio_id'] ) ? $_POST['evogt_audio_id'] : 0, 'audio/' );
    foreach ( array( $t_id, $a_id ) as $check ) {
        if ( is_wp_error( $check ) ) {
            wp_safe_redirect( add_query_arg( array( 'evogt_error' => 'attachment', 'evogt_detail' => rawurlencode( $check->get_error_message() ) ), $edit_url ) );
            exit;
        }
    }

    try {
        $result = evogt_update_work( $id, array(
            'title'                       => $title,
            'comment'                     => $comment,
            'transcription_attachment_id' => $t_id,
            'audio_attachment_id'         => $a_id,
        ) );
    } catch ( PDOException $e ) {
        error_log( 'evogt: save work ' . $id . ' failed: ' . $e->getMessage() );
        $result = new WP_Error( 'db', $e->getMessage() );
    }

    if ( is_wp_error( $result ) ) {
        wp_safe_redirect( add_query_arg( 'evogt_error', 'db', $edit_url ) );
        exit;
    }

    wp_safe_redirect( add_query_arg( 'updated', 1, $edit_url ) );
    exit;
}
