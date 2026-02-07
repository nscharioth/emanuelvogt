let allWorks = [];
const searchInput = document.getElementById('searchInput');
const genreFilter = document.getElementById('genreFilter');
const instrumentationFilter = document.getElementById('instrumentationFilter');
const resultsGrid = document.getElementById('resultsGrid');
const viewerModal = document.getElementById('viewerModal');
const statsCounter = document.getElementById('statsCounter');

// Initial Load
async function init() {
    await fetchGenres();
    await fetchInstrumentations();
    await performSearch();
}

async function fetchGenres() {
    const res = await fetch('/api/genres');
    const genres = await res.json();
    genreFilter.innerHTML = genres.map(g => `<option value="${g}">${g === 'All' ? 'Alle Gattungen' : g}</option>`).join('');
}

async function fetchInstrumentations() {
    const res = await fetch('/api/instrumentations');
    const instrumentations = await res.json();
    instrumentationFilter.innerHTML = instrumentations.map(i => `<option value="${i}">${i === 'All' ? 'Alle Besetzungen' : i}</option>`).join('');
}

async function performSearch() {
    const query = searchInput.value;
    const genre = genreFilter.value;
    const instrumentation = instrumentationFilter.value;

    const res = await fetch(`/api/works?q=${encodeURIComponent(query)}&genre=${encodeURIComponent(genre)}&instrumentation=${encodeURIComponent(instrumentation)}`);
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
    const res = await fetch(`/api/work/${workId}`);
    const work = await res.json();

    document.getElementById('modalWorkNum').innerText = work.work_number;
    document.getElementById('modalTitle').innerText = work.title;

    const fileList = document.getElementById('fileList');
    fileList.innerHTML = work.files.map(file => `
        <div class="file-item" onclick="loadPDF(${file.id}, this)">
            <p>${file.filename}</p>
            <small>${(file.size / 1024 / 1024).toFixed(2)} MB</small>
        </div>
    `).join('');

    // Show MusicXML notice if available
    const musicxmlNotice = document.getElementById('musicxmlNotice');
    if (work.has_musicxml) {
        musicxmlNotice.style.display = 'block';
        const musicxmlLink = document.getElementById('musicxmlLink');
        musicxmlLink.href = `/musicxml-player?work=${encodeURIComponent(work.work_number)}`;
    } else {
        musicxmlNotice.style.display = 'none';
    }

    // Clear prev viewer
    document.getElementById('pdfFrame').src = '';
    document.getElementById('pdfFrame').style.display = 'none';
    document.getElementById('viewerPlaceholder').style.display = 'block';

    viewerModal.style.display = 'block';

    // Auto-load if only one file
    if (work.files.length === 1) {
        loadPDF(work.files[0].id, fileList.firstElementChild);
    }
}

function loadPDF(fileId, element) {
    // UI Update
    document.querySelectorAll('.file-item').forEach(i => i.classList.remove('active'));
    element.classList.add('active');

    // Load iframe
    const pdfFrame = document.getElementById('pdfFrame');
    const placeholder = document.getElementById('viewerPlaceholder');

    pdfFrame.src = `/pdf/${fileId}#toolbar=0&navpanes=0&scrollbar=0`;
    pdfFrame.style.display = 'block';
    placeholder.style.display = 'none';
}

function closeViewer() {
    viewerModal.style.display = 'none';
    document.getElementById('pdfFrame').src = '';
}

// Event Listeners
let debounceTimer;
searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(performSearch, 300);
});

genreFilter.addEventListener('change', performSearch);
instrumentationFilter.addEventListener('change', performSearch);

// Close on escape
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeViewer();
});

// Start
init();
