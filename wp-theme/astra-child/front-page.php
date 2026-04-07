<?php
/**
 * The template for displaying the front page (Archive Application)
 */

get_header(); ?>

<div class="app-container">
    <!-- Header Section -->
    <header class="main-header" style="position: relative;">
        <!-- Top right global MusicXML Player button -->
        <a href="/musicxml-player" style="position: absolute; right: 0; top: 0; display: inline-block; padding: 10px 20px; background: rgba(212, 175, 55, 0.2); color: #d4af37; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 0.95rem; border: 1px solid rgba(212, 175, 55, 0.4); transition: all 0.3s;" onmouseover="this.style.background='rgba(212, 175, 55, 0.3)'" onmouseout="this.style.background='rgba(212, 175, 55, 0.2)'">
            🎵 MusicXML Player
        </a>
        <div class="search-controls" style="margin-top: 3.5rem;">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Suche nach Titel oder Werknummer..." autocomplete="off">
                <span class="search-icon">🔍</span>
            </div>
            <select id="genreFilter" class="genre-select">
                <option value="All">Alle Gattungen</option>
            </select>
            <select id="instrumentationFilter" class="genre-select">
                <option value="All">Alle Besetzungen</option>
            </select>
        </div>
        
        <div class="stats" id="statsCounter">
            Lade Archiv...
        </div>
    </header>

    <!-- Content Area -->
    <main class="content-grid" id="resultsGrid">
        <!-- Cards will be injected here -->
    </main>

    <!-- PDF Viewer Modal -->
    <div id="viewerModal" class="modal">
        <div class="modal-content">
            <header class="modal-header">
                <div class="modal-info">
                    <span class="work-num" id="modalWorkNum"></span>
                    <h2 id="modalTitle"></h2>
                </div>
                <button class="close-btn" onclick="closeViewer()">&times;</button>
            </header>
            <div class="viewer-body">
                <div class="file-sidebar" id="fileList">
                    <!-- File buttons -->
                </div>
                <div class="pdf-frame">
                    <div id="musicxmlNotice" style="display: none; padding: 15px; background: rgba(74, 144, 226, 0.1); border-left: 4px solid #4a90e2; margin-bottom: 15px; border-radius: 4px;">
                        <strong>🎵 MusicXML verfügbar!</strong>
                        <p style="margin: 5px 0 0 0; font-size: 0.9rem;">Dieses Werk ist als interaktive Notenansicht verfügbar.</p>
                        <a id="musicxmlLink" href="/musicxml-player" target="_blank" style="display: inline-block; margin-top: 8px; padding: 8px 16px; background: #4a90e2; color: white; text-decoration: none; border-radius: 6px; font-size: 0.9rem;">
                            Noten anzeigen & abspielen
                        </a>
                    </div>
                    <div class="pdf-viewer-area">
                        <div id="pdfRotationWrapper" class="pdf-rotation-wrapper">
                            <iframe id="pdfFrame" src="" frameborder="0"></iframe>
                        </div>
                        <div id="viewerPlaceholder" class="placeholder">
                            <p>Wählen Sie eine Datei zur Ansicht aus</p>
                        </div>
                    </div>
                    <?php if (current_user_can('edit_posts')) : ?>
                    <div id="rotationControls" style="display: none; padding: 10px; background: rgba(0,0,0,0.8); border-top: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; gap: 10px; flex-shrink: 0;">
                        <span style="font-size: 0.9rem; font-weight: 600; color: #ccc;">PDF Rotation (Admin):</span>
                        <button onclick="rotatePDF(0)" class="rotation-btn" data-rotation="0">0°</button>
                        <button onclick="rotatePDF(90)" class="rotation-btn" data-rotation="90">90°</button>
                        <button onclick="rotatePDF(180)" class="rotation-btn" data-rotation="180">180°</button>
                        <button onclick="rotatePDF(270)" class="rotation-btn" data-rotation="270">270°</button>
                        <button onclick="saveRotation()" class="save-rotation-btn" style="margin-left: auto; padding: 8px 16px; background: #4a90e2; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 600;">💾 Speichern</button>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>
</div>

<?php get_footer(); ?>
