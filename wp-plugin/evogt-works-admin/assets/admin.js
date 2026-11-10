/* Media pickers for the "Neusatz (PDF)" and "Aufnahme (MP3)" fields. */
(function ($) {
    'use strict';

    function iconFor(mime) {
        return mime === 'audio' ? 'dashicons-format-audio' : 'dashicons-media-document';
    }

    function renderPreview($field, attachment) {
        var mime = $field.data('mime');
        var meta = mime === 'audio'
            ? (attachment.fileLength || '')
            : (attachment.filesizeHumanReadable || '');
        var html = '<span class="dashicons ' + iconFor(mime) + '"></span> ' +
            '<a href="' + attachment.url + '" target="_blank" rel="noopener"></a> ' +
            '<span class="evogt-muted"></span>';
        var $preview = $field.find('.evogt-media-preview').html(html);
        $preview.find('a').text(attachment.title || attachment.filename || attachment.url);
        $preview.find('.evogt-muted').text((meta ? meta + ' · ' : '') + 'Mediathek #' + attachment.id);
    }

    $(document).on('click', '.evogt-media-select', function (e) {
        e.preventDefault();
        var $field = $(this).closest('.evogt-media-field');
        var mime = $field.data('mime');

        var frame = wp.media({
            title: $field.data('title') || 'Datei auswählen',
            button: { text: 'Übernehmen' },
            library: { type: mime },
            multiple: false
        });

        frame.on('select', function () {
            var attachment = frame.state().get('selection').first().toJSON();
            var ok = mime === 'audio'
                ? (attachment.mime || '').indexOf('audio/') === 0
                : attachment.mime === 'application/pdf';
            if (!ok) {
                window.alert(mime === 'audio'
                    ? 'Bitte eine Audiodatei (z. B. MP3) auswählen.'
                    : 'Bitte eine PDF-Datei auswählen.');
                return;
            }
            $field.find('.evogt-media-id').val(attachment.id);
            renderPreview($field, attachment);
            $field.find('.evogt-media-remove').prop('hidden', false);
        });

        frame.open();
    });

    $(document).on('click', '.evogt-media-remove', function (e) {
        e.preventDefault();
        var $field = $(this).closest('.evogt-media-field');
        $field.find('.evogt-media-id').val(0);
        $field.find('.evogt-media-preview').html('<span class="evogt-muted">Keine Datei ausgewählt.</span>');
        $(this).prop('hidden', true);
    });
})(jQuery);
