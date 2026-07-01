<?php
/**
 * The template for displaying the front page (Archive Application)
 */

get_header(); ?>

<div class="app-container">
    <!-- Header Section -->
    <header class="main-header" style="position: relative;">
        <div class="search-controls" style="margin-top: 3.5rem;">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Suche nach Titel, Werknummer, Gattung oder Besetzung..." autocomplete="off">
                <span class="search-icon">🔍</span>
            </div>
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
