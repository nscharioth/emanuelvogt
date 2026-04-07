let allWorks = [];
let currentFileId = null;
let currentRotation = 0;
const searchInput = document.getElementById('searchInput');
const genreFilter = document.getElementById('genreFilter');
const instrumentationFilter = document.getElementById('instrumentationFilter');
const resultsGrid = document.getElementById('resultsGrid');
const viewerModal = document.getElementById('viewerModal');
const statsCounter = document.getElementById('statsCounter');

const API_BASE = window.evogtSettings ? window.evogtSettings.apiUrl : '/api';
// We don't always need pdfBaseUrl immediately since the API returns absolute URLs for files, 
// but we keep it just in case.

// Initial Load
async function init() {
    await fetchGenres();
    await fetchInstrumentations();
    await performSearch();
}

async function fetchGenres() {
    const res = await fetch(`${API_BASE}/genres`);
    const genres = await res.json();
    genreFilter.innerHTML = genres.map(g => `<option value="${g}">${g === 'All' ? 'Alle Gattungen' : g}</option>`).join('');
}

async function fetchInstrumentations() {
    const res = await fetch(`${API_BASE}/instrumentations`);
    const instrumentations = await res.json();
    instrumentationFilter.innerHTML = instrumentations.map(i => `<option value="${i}">${i === 'All' ? 'Alle Besetzungen' : i}</option>`).join('');
}

async function performSearch() {
    const query = searchInput.value;
    const genre = genreFilter.value;
    const instrumentation = instrumentationFilter.value;

    const res = await fetch(`${API_BASE}/works?q=${encodeURIComponent(query)}&genre=${encodeURIComponent(genre)}&instrumentation=${encodeURIComponent(instrumentation)}`);
    const works = await res.json();
    renderWorks(works);
    statsCounter.innerText = `${works.length} Werke gefunden`;
}

function renderWorks(works) {
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

async function openWorkDetail(workId) {
    const res = await fetch(`${API_BASE}/work/${workId}`);
    const work = await res.json();

    document.getElementById('modalWorkNum').innerText = work.work_number;
    document.getElementById('modalTitle').innerText = work.title;

    const fileList = document.getElementById('fileList');
    fileList.innerHTML = work.files.map(file => {
        const safeFilename = file.filename.replace(/'/g, "\\'").replace(/"/g, '&quot;');
        const safeUrl = file.url.replace(/'/g, "\\'");
        return `
        <div class="file-item" onclick="loadFile(${file.id}, ${file.rotation || 0}, '${safeFilename}', '${safeUrl}', this)">
            <p>${file.filename}</p>
            <small>${(file.size / 1024 / 1024).toFixed(2)} MB</small>
        </div>
        `;
    }).join('');

    const musicxmlNotice = document.getElementById('musicxmlNotice');
    if (work.has_musicxml) {
        musicxmlNotice.style.display = 'block';
        const musicxmlLink = document.getElementById('musicxmlLink');
        musicxmlLink.href = `/musicxml-player?work=${encodeURIComponent(work.work_number)}`;
    } else {
        musicxmlNotice.style.display = 'none';
    }

    document.getElementById('pdfFrame').src = '';
    document.getElementById('pdfFrame').style.display = 'none';
    document.getElementById('viewerPlaceholder').style.display = 'block';

    viewerModal.style.display = 'block';

    if (work.files.length === 1) {
        const safeFilename = work.files[0].filename.replace(/'/g, "\\'").replace(/"/g, '&quot;');
        const safeUrl = work.files[0].url.replace(/'/g, "\\'");
        loadFile(work.files[0].id, work.files[0].rotation || 0, work.files[0].filename, work.files[0].url, fileList.firstElementChild);
    }
}

function loadFile(fileId, rotation, filename, fileUrl, element) {
    currentFileId = fileId;
    currentRotation = rotation;

    document.querySelectorAll('.file-item').forEach(i => i.classList.remove('active'));
    element.classList.add('active');

    const isImage = /\.(jpg|jpeg|png|gif)$/i.test(filename);
    
    const pdfFrame = document.getElementById('pdfFrame');
    const placeholder = document.getElementById('viewerPlaceholder');
    const rotationControls = document.getElementById('rotationControls');

    // Reset iframe class
    pdfFrame.className = '';

    if (isImage) {
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

        // Use direct static fileUrl (bypassing backend rotation engine)
        // Add PDF.js hashtag parameters.
        pdfFrame.src = `${fileUrl}#toolbar=0&navpanes=0&scrollbar=0`;
        pdfFrame.style.display = 'block';
        placeholder.style.display = 'none';

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
}

if (genreFilter) genreFilter.addEventListener('change', performSearch);
if (instrumentationFilter) instrumentationFilter.addEventListener('change', performSearch);

window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeViewer();
});

// Start
init();
