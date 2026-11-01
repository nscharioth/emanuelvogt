let allWorks = [];
let currentFileId = null;
let currentRotation = 0;
const searchInput = document.getElementById('searchInput');
const resultsGrid = document.getElementById('resultsGrid');
const viewerModal = document.getElementById('viewerModal');
const statsCounter = document.getElementById('statsCounter');
const searchIcon = document.querySelector('.search-icon');

const API_BASE = window.evogtSettings ? window.evogtSettings.apiUrl : '/api';
// We don't always need pdfBaseUrl immediately since the API returns absolute URLs for files, 
// but we keep it just in case.

// Initial Load
async function init() {
    renderEmptyState();
}

function renderEmptyState(message = 'Suche starten oder das gesamte Archiv bei Bedarf laden.') {
    resultsGrid.innerHTML = `
        <div class="empty-state">
            <p>${message}</p>
            <button type="button" class="load-all-btn" id="loadAllWorksBtn">Alle Werke laden</button>
        </div>
        <section class="recordings-section" id="recordingsSection" style="display: none;"></section>
    `;
    statsCounter.innerText = 'Archiv bereit';

    const loadAllButton = document.getElementById('loadAllWorksBtn');
    if (loadAllButton) {
        loadAllButton.addEventListener('click', () => performSearch({ forceFullLoad: true }));
    }

    renderRecordings();
}

// Recordings (MP3s from the media library) — fetched once, then served from memory
let recordingsCache = null;

async function renderRecordings() {
    if (recordingsCache === null) {
        try {
            const res = await fetch(`${API_BASE}/recordings`);
            recordingsCache = res.ok ? await res.json() : [];
        } catch (err) {
            console.error('Recordings load error:', err);
            recordingsCache = [];
        }
    }

    // The empty state may have been replaced by search results in the meantime
    const section = document.getElementById('recordingsSection');
    if (!section || !recordingsCache.length) return;

    section.innerHTML = `
        <h2 class="recordings-heading">Aufnahmen</h2>
        <div class="recordings-grid">
            ${recordingsCache.map(rec => `
                <div class="work-card recording-card" onclick="openWorkDetail(${rec.work_id}, { autoplayAudio: true })">
                    <div class="card-header">
                        <span class="card-number">${rec.work_number}</span>
                        <span class="card-genre">${rec.genre || ''}</span>
                    </div>
                    <h3 class="card-title">${rec.title}</h3>
                    <div class="recording-meta">
                        <span class="recording-play">▶</span>
                        <span>${rec.length_formatted || ''}</span>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    section.style.display = '';
}

// Escape a value for use inside a single-quoted onclick argument
function jsArg(value) {
    return String(value).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

async function performSearch(options = {}) {
    const query = searchInput.value.trim();
    const forceFullLoad = options.forceFullLoad === true;

    if (!query && !forceFullLoad) {
        renderEmptyState();
        return;
    }

    // Show loading indicator while fetching
    resultsGrid.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div><br>Lade Archiv…</div>';

    const res = await fetch(`${API_BASE}/works?q=${encodeURIComponent(query)}`);
    const works = await res.json();
    renderWorks(works);
    statsCounter.innerText = query ? `${works.length} Werke gefunden` : `${works.length} Werke geladen`;
}

function renderWorks(works) {
    if (!works.length) {
        renderEmptyState('Keine Werke gefunden. Bitte Suche anpassen.');
        return;
    }

    resultsGrid.innerHTML = works.map((work, index) => `
        <div class="work-card" onclick="openWorkDetail(${work.id})" style="animation: gridFadeIn 0.5s ease-out ${index * 0.01}s both">
            <div class="card-header">
                <span class="card-number">${work.work_number}</span>
                <span class="card-genre">${work.genre || ''}</span>
            </div>
            <h3 class="card-title">${work.title}</h3>
        </div>
    `).join('');
}

async function openWorkDetail(workId, options = {}) {
    const res = await fetch(`${API_BASE}/work/${workId}`);
    const work = await res.json();
    const transcriptions = work.transcriptions || [];
    const audio = work.audio || [];

    document.getElementById('modalWorkNum').innerText = work.work_number;
    document.getElementById('modalTitle').innerText = work.title;

    const fileList = document.getElementById('fileList');
    const originalItems = work.files.map(file => `
        <div class="file-item" onclick="loadFile(${file.id}, ${file.rotation || 0}, '${jsArg(file.filename)}', '${jsArg(file.url)}', this)">
            <p>${file.filename}</p>
            <small>${(file.size / 1024 / 1024).toFixed(2)} MB</small>
        </div>
    `);
    // Transcriptions and audio come from the WP media library (attachment IDs, no rotation)
    const transcriptionItems = transcriptions.map(t => `
        <div class="file-item file-item--transcription" onclick="loadFile(0, 0, '${jsArg(t.title)}', '${jsArg(t.url)}', this, 'transcription')">
            <p>Neusatz (PDF)</p>
            <small>${t.title}</small>
        </div>
    `);
    const audioItems = audio.map(a => `
        <div class="file-item file-item--audio" onclick="loadFile(0, 0, '${jsArg(a.title)}', '${jsArg(a.url)}', this, 'audio')">
            <p>♪ Aufnahme anhören</p>
            <small>${a.length_formatted || a.title}</small>
        </div>
    `);
    fileList.innerHTML = [...originalItems, ...transcriptionItems, ...audioItems].join('');

    stopAudio();
    document.getElementById('pdfFrame').src = '';
    document.getElementById('pdfFrame').style.display = 'none';
    document.getElementById('viewerPlaceholder').style.display = 'block';

    viewerModal.style.display = 'block';

    if (options.autoplayAudio && audio.length) {
        loadFile(0, 0, audio[0].title, audio[0].url, fileList.querySelector('.file-item--audio'), 'audio');
    } else if (work.files.length === 1) {
        loadFile(work.files[0].id, work.files[0].rotation || 0, work.files[0].filename, work.files[0].url, fileList.firstElementChild);
    }
}

function stopAudio() {
    const audioElement = document.getElementById('audioElement');
    if (!audioElement) return;
    audioElement.pause();
    audioElement.removeAttribute('src');
    audioElement.load();
    document.getElementById('audioPlayer').style.display = 'none';
}

function loadFile(fileId, rotation, filename, fileUrl, element, kind = 'original') {
    // Rotation is stored per archive file; media library items have none
    currentFileId = kind === 'original' ? fileId : null;
    currentRotation = kind === 'original' ? rotation : 0;

    document.querySelectorAll('.file-item').forEach(i => i.classList.remove('active'));
    element.classList.add('active');

    const isImage = /\.(jpg|jpeg|png|gif)$/i.test(filename);
    const isMobile = window.innerWidth < 768 || navigator.maxTouchPoints > 0;

    const pdfFrame = document.getElementById('pdfFrame');
    const placeholder = document.getElementById('viewerPlaceholder');
    const rotationControls = document.getElementById('rotationControls');
    const pdfOpenLink = document.getElementById('pdfOpenLink');

    // Reset iframe class
    pdfFrame.className = '';

    if (kind !== 'original') {
        if (rotationControls) rotationControls.style.display = 'none';
        document.getElementById('pdfRotationWrapper').style.transform = '';
    }

    if (pdfOpenLink) {
        pdfOpenLink.textContent = kind === 'audio' ? '♪ Aufnahme in neuem Tab öffnen' : '📄 PDF in neuem Tab öffnen';
    }

    if (kind === 'audio') {
        pdfFrame.src = '';
        pdfFrame.style.display = 'none';
        placeholder.style.display = 'none';
        if (pdfOpenLink) pdfOpenLink.href = fileUrl;

        const audioElement = document.getElementById('audioElement');
        document.getElementById('audioTitle').innerText = filename;
        document.getElementById('audioPlayer').style.display = 'flex';
        if (audioElement.getAttribute('src') !== fileUrl) audioElement.src = fileUrl;
        // Autoplay may be blocked by the browser; the controls stay usable either way
        audioElement.play().catch(() => {});
        return;
    }

    stopAudio();

    if (kind === 'transcription') {
        const pdfSrc = isMobile ? fileUrl : `${fileUrl}#toolbar=0&navpanes=0&scrollbar=0`;
        pdfFrame.src = pdfSrc;
        pdfFrame.style.display = 'block';
        placeholder.style.display = 'none';
        if (pdfOpenLink) pdfOpenLink.href = fileUrl;
    } else if (isImage) {
        if (rotationControls) rotationControls.style.display = 'none';
        pdfFrame.src = fileUrl;
        pdfFrame.style.display = 'block';
        placeholder.style.display = 'none';
        rotatePDF(0); // Reset visual rotation
    } else {
        if (rotationControls) rotationControls.style.display = 'flex';

        document.querySelectorAll('.rotation-btn').forEach(btn => {
            btn.classList.toggle('active', parseInt(btn.dataset.rotation) === rotation);
        });

        // On mobile: allow native PDF controls (don't suppress toolbar).
        // On desktop: hide chrome toolbar for cleaner embed.
        const pdfSrc = isMobile ? fileUrl : `${fileUrl}#toolbar=0&navpanes=0&scrollbar=0`;
        pdfFrame.src = pdfSrc;
        pdfFrame.style.display = 'block';
        placeholder.style.display = 'none';

        // Update the mobile "open in new tab" link
        const pdfOpenLink = document.getElementById('pdfOpenLink');
        if (pdfOpenLink) pdfOpenLink.href = fileUrl;

        // Apply visual rotation based on DB initial value!
        rotatePDF(rotation);
    }
}

function rotatePDF(degrees) {
    if (!currentFileId) return;
    currentRotation = degrees;
    
    document.querySelectorAll('.rotation-btn').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.rotation) === degrees);
    });

    // In WP, we don't have python PyPDF2 on the fly, we rely entirely on CSS!
    const wrapper = document.getElementById('pdfRotationWrapper');
    wrapper.style.transform = `rotate(${degrees}deg)`;
}

async function saveRotation() {
    if (!currentFileId) return;

    try {
        const res = await fetch(`${API_BASE}/pdf-rotation/${currentFileId}`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                // Adding this for WP nonce if needed, but endpoint is open for testing or we check edit_posts
                'X-WP-Nonce': window.evogtSettings ? window.evogtSettings.nonce : ''
            },
            body: JSON.stringify({ rotation: currentRotation })
        });

        if (res.ok) {
            const saveBtn = document.querySelector('.save-rotation-btn');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '✓ Gespeichert';
            saveBtn.style.background = '#22c55e';
            setTimeout(() => {
                saveBtn.textContent = originalText;
                saveBtn.style.background = '#4a90e2';
            }, 2000);
        } else {
            alert('Fehler beim Speichern der Rotation. Nur Administratoren dürfen dies speichern.');
        }
    } catch (err) {
        console.error('Save rotation error:', err);
        alert('Fehler beim Speichern der Rotation');
    }
}

function closeViewer() {
    if (!viewerModal) return;
    viewerModal.style.display = 'none';
    document.getElementById('pdfFrame').src = '';
    stopAudio();
    const rotationControls = document.getElementById('rotationControls');
    if (rotationControls) rotationControls.style.display = 'none';
    currentFileId = null;
    currentRotation = 0;
}

let debounceTimer;
if (searchInput) {
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(performSearch, 300);
    });

    searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            clearTimeout(debounceTimer);
            performSearch();
        }
    });
}

if (searchIcon) {
    searchIcon.addEventListener('click', () => {
        performSearch({ forceFullLoad: !searchInput.value.trim() });
    });
}

window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeViewer();
});

// Close modal when tapping the dark backdrop on mobile
if (viewerModal) {
    viewerModal.addEventListener('click', (e) => {
        if (e.target === viewerModal) closeViewer();
    });
}

// Start — script is in footer so DOM is ready, but guard readyState for safety
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
