/* ═══════════════════════════════════════════════════════
   PDF Text Editor — app.js
   Uses:  PDF.js  → render pages + extract text positions
          pdf-lib → write edits back into the PDF on save
═══════════════════════════════════════════════════════ */

pdfjsLib.GlobalWorkerOptions.workerSrc =
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// ─────────────────────────────────────────
// App state
// ─────────────────────────────────────────
let pdfJsDoc   = null;
let pdfBytes   = null;
let fileName   = 'document';
const SCALE    = 1.5;

const edits     = {};   // { pageNum: { itemIdx: editData } }
const pageItems = {};   // { pageNum: [item, …] }
let   activeDiv = null;

const style = {
  fontSize:   12,
  fontFamily: 'Helvetica',
  bold:       false,
  italic:     false,
  color:      '#000000',
};

// ─────────────────────────────────────────
// DOM refs
// ─────────────────────────────────────────
const uploadScreen   = document.getElementById('upload-screen');
const editorScreen   = document.getElementById('editor-screen');
const fileInput      = document.getElementById('file-input');
const dropZone       = document.getElementById('drop-zone');
const pagesContainer = document.getElementById('pages-container');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingText    = document.getElementById('loading-text');
const fileNameLabel  = document.getElementById('file-name-label');
const fontFamilySel  = document.getElementById('font-family');
const fontSizeInput  = document.getElementById('font-size');
const btnBold        = document.getElementById('btn-bold');
const btnItalic      = document.getElementById('btn-italic');
const textColorInput = document.getElementById('text-color');

// ═══════════════════════════════════════════════════════
// 1.  FILE UPLOAD
// ═══════════════════════════════════════════════════════

document.getElementById('choose-file-btn').addEventListener('click', () => fileInput.click());

dropZone.addEventListener('click', e => {
  if (e.target.id !== 'choose-file-btn') fileInput.click();
});
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type === 'application/pdf') openPDF(file);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) openPDF(fileInput.files[0]);
});

document.getElementById('back-btn').addEventListener('click', () => {
  pdfJsDoc = null;
  pdfBytes = null;
  Object.keys(edits).forEach(k => delete edits[k]);
  Object.keys(pageItems).forEach(k => delete pageItems[k]);
  activeDiv = null;
  pagesContainer.innerHTML = '';
  fileInput.value = '';
  editorScreen.classList.add('hidden');
  uploadScreen.classList.remove('hidden');
});

// ═══════════════════════════════════════════════════════
// 2.  LOAD & RENDER PDF
// ═══════════════════════════════════════════════════════

async function openPDF(file) {
  showLoading('Loading PDF…');
  try {
    fileName  = file.name.replace(/\.pdf$/i, '');
    pdfBytes  = await file.arrayBuffer();
    fileNameLabel.textContent = file.name;

    pdfJsDoc = await pdfjsLib.getDocument({ data: pdfBytes.slice(0) }).promise;

    uploadScreen.classList.add('hidden');
    editorScreen.classList.remove('hidden');

    await renderAll();
    hideLoading();
  } catch (err) {
    hideLoading();
    console.error(err);
    alert('Could not open this PDF.\n\n' + err.message);
  }
}

async function renderAll() {
  pagesContainer.innerHTML = '';
  for (let p = 1; p <= pdfJsDoc.numPages; p++) {
    loadingText.textContent = `Rendering page ${p} of ${pdfJsDoc.numPages}…`;
    await renderPage(p);
  }
}

async function renderPage(pageNum) {
  const page     = await pdfJsDoc.getPage(pageNum);
  const viewport = page.getViewport({ scale: SCALE });

  const wrapper = document.createElement('div');
  wrapper.className    = 'page-wrapper';
  wrapper.dataset.page = pageNum;

  // ── Canvas ──────────────────────────────
  const canvas = document.createElement('canvas');
  canvas.width  = viewport.width;
  canvas.height = viewport.height;
  await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;

  // ── Transparent text overlay ────────────
  const overlay = document.createElement('div');
  overlay.className    = 'text-layer';
  overlay.style.width  = viewport.width  + 'px';
  overlay.style.height = viewport.height + 'px';

  const textContent = await page.getTextContent();
  pageItems[pageNum] = textContent.items;

  // Pass the rendered canvas so each div can sample its background colour
  textContent.items.forEach((item, idx) => {
    if (!item.str.trim()) return;
    const el = buildTextDiv(item, idx, pageNum, viewport, canvas);
    if (el) overlay.appendChild(el);
  });

  const label = document.createElement('div');
  label.className   = 'page-label';
  label.textContent = `Page ${pageNum}`;

  wrapper.appendChild(canvas);
  wrapper.appendChild(overlay);
  pagesContainer.appendChild(wrapper);
  pagesContainer.appendChild(label);
}

// ─────────────────────────────────────────
// Sample the dominant background colour from the canvas at a text position.
// Averages all pixels in the bounding box — since most pixels in a text cell
// are background rather than ink, the average is a good approximation.
// ─────────────────────────────────────────
function sampleBgColor(canvas, x, y, w, h) {
  const ctx = canvas.getContext('2d');
  const sx  = Math.max(0, Math.round(x));
  const sy  = Math.max(0, Math.round(y));
  const sw  = Math.min(Math.max(1, Math.round(w)), canvas.width  - sx);
  const sh  = Math.min(Math.max(2, Math.round(h)), canvas.height - sy);
  if (sw <= 0 || sh <= 0) return '#ffffff';

  try {
    const data = ctx.getImageData(sx, sy, sw, sh).data;
    let r = 0, g = 0, b = 0, n = 0;
    // Sample every 4th pixel for speed
    for (let i = 0; i < data.length; i += 16) {
      r += data[i]; g += data[i + 1]; b += data[i + 2]; n++;
    }
    if (!n) return '#ffffff';
    return '#' + [r, g, b]
      .map(v => Math.round(v / n).toString(16).padStart(2, '0'))
      .join('');
  } catch { return '#ffffff'; }
}

// ─────────────────────────────────────────
// Build one transparent click-target div
// ─────────────────────────────────────────
function buildTextDiv(item, idx, pageNum, viewport, canvas) {
  const [a, b, c, d, e, f] = item.transform;

  const pdfFontSize = Math.abs(d) || Math.abs(a);
  if (pdfFontSize < 1) return null;

  const screenLeft = e * SCALE;
  const screenTop  = viewport.height - f * SCALE - pdfFontSize * SCALE;
  const screenW    = (item.width || pdfFontSize * item.str.length * 0.6) * SCALE;
  const screenH    = pdfFontSize * SCALE * 1.3;  // tall enough to cover descenders

  // Sample the background colour from the already-rendered canvas
  const bgColor = canvas
    ? sampleBgColor(canvas, screenLeft, screenTop, screenW + 4, screenH)
    : '#ffffff';

  const div = document.createElement('div');
  div.className       = 'text-item';
  div.contentEditable = 'false';
  div.textContent     = item.str;

  div.dataset.original = item.str;
  div.dataset.page     = pageNum;
  div.dataset.idx      = idx;
  div.dataset.pdfX     = e;
  div.dataset.pdfY     = f;
  div.dataset.pdfW     = item.width  || 0;
  div.dataset.pdfH     = item.height || pdfFontSize;
  div.dataset.pdfFs    = pdfFontSize;
  div.dataset.bgColor  = bgColor;   // ← stored for editing + PDF export

  div.style.left     = screenLeft + 'px';
  div.style.top      = screenTop  + 'px';
  div.style.width    = (screenW + 4) + 'px';
  div.style.height   = screenH + 'px';
  div.style.fontSize = (pdfFontSize * SCALE) + 'px';

  // ── Events ───────────────────────────────
  div.addEventListener('click',   ev => { ev.stopPropagation(); startEdit(div); });
  div.addEventListener('blur',    ()  => commitEdit(div));
  div.addEventListener('keydown', ev => {
    if (ev.key === 'Escape') { div.textContent = div.dataset.original; div.blur(); }
    if (ev.key === 'Enter' && !ev.shiftKey) { ev.preventDefault(); div.blur(); }
  });
  div.addEventListener('input', () => { div.style.width = 'auto'; });

  return div;
}

// ═══════════════════════════════════════════════════════
// 3.  EDITING
// ═══════════════════════════════════════════════════════

function startEdit(div) {
  if (activeDiv && activeDiv !== div) {
    activeDiv.contentEditable = 'false';
    activeDiv.classList.remove('editing');
    finaliseStyle(activeDiv);
  }

  activeDiv = div;

  const pageNum = parseInt(div.dataset.page);
  const idx     = parseInt(div.dataset.idx);
  const saved   = edits[pageNum]?.[idx];

  style.fontSize   = saved?.fontSize   ?? parseFloat(div.dataset.pdfFs);
  style.fontFamily = saved?.fontFamily ?? 'Helvetica';
  style.bold       = saved?.bold       ?? false;
  style.italic     = saved?.italic     ?? false;
  style.color      = saved?.color      ?? '#000000';

  syncToolbar();
  applyStyleToDiv(div);

  // Cover the original canvas text with the sampled background colour
  div.style.background = div.dataset.bgColor || '#ffffff';

  div.contentEditable = 'true';
  div.classList.add('editing');
  div.focus();

  // Select all text so the user can type immediately
  const range = document.createRange();
  range.selectNodeContents(div);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
}

function commitEdit(div) {
  div.contentEditable = 'false';
  div.classList.remove('editing');
  if (activeDiv === div) activeDiv = null;

  const text = div.textContent;
  const orig = div.dataset.original;

  if (text !== orig) {
    div.classList.add('modified');
    storeEdit(div);
    finaliseStyle(div);
  } else {
    // Nothing changed — revert to invisible (original canvas text shows through)
    const pageNum = parseInt(div.dataset.page);
    const idx     = parseInt(div.dataset.idx);
    if (edits[pageNum]) delete edits[pageNum][idx];
    div.classList.remove('modified');
    resetDivStyle(div);
  }
}

function storeEdit(div) {
  const pageNum = parseInt(div.dataset.page);
  const idx     = parseInt(div.dataset.idx);
  if (!edits[pageNum]) edits[pageNum] = {};

  edits[pageNum][idx] = {
    newText:      div.textContent,
    fontSize:     style.fontSize,
    fontFamily:   style.fontFamily,
    bold:         style.bold,
    italic:       style.italic,
    color:        style.color,
    bgColor:      div.dataset.bgColor || '#ffffff',  // used for PDF cover rect
    x:            parseFloat(div.dataset.pdfX),
    y:            parseFloat(div.dataset.pdfY),
    w:            parseFloat(div.dataset.pdfW),
    h:            parseFloat(div.dataset.pdfH),
    origFontSize: parseFloat(div.dataset.pdfFs),
  };
}

// Click anywhere outside a text item → commit current edit
document.addEventListener('click', () => { if (activeDiv) activeDiv.blur(); });

// ═══════════════════════════════════════════════════════
// 4.  TOOLBAR
// ═══════════════════════════════════════════════════════

fontFamilySel.addEventListener('change', () => {
  style.fontFamily = fontFamilySel.value;
  if (activeDiv) applyStyleToDiv(activeDiv);
});

fontSizeInput.addEventListener('change', () => {
  const v = parseFloat(fontSizeInput.value);
  if (v >= 4 && v <= 144) { style.fontSize = v; if (activeDiv) applyStyleToDiv(activeDiv); }
});

document.getElementById('font-size-down').addEventListener('click', () => {
  const v = parseFloat(fontSizeInput.value) - 1;
  if (v >= 4) { fontSizeInput.value = v; style.fontSize = v; if (activeDiv) applyStyleToDiv(activeDiv); }
});
document.getElementById('font-size-up').addEventListener('click', () => {
  const v = parseFloat(fontSizeInput.value) + 1;
  if (v <= 144) { fontSizeInput.value = v; style.fontSize = v; if (activeDiv) applyStyleToDiv(activeDiv); }
});

btnBold.addEventListener('click', () => {
  style.bold = !style.bold;
  btnBold.classList.toggle('active', style.bold);
  if (activeDiv) applyStyleToDiv(activeDiv);
});

btnItalic.addEventListener('click', () => {
  style.italic = !style.italic;
  btnItalic.classList.toggle('active', style.italic);
  if (activeDiv) applyStyleToDiv(activeDiv);
});

textColorInput.addEventListener('input', () => {
  style.color = textColorInput.value;
  if (activeDiv) applyStyleToDiv(activeDiv);
});

// ─── Helpers ─────────────────────────────

function syncToolbar() {
  fontSizeInput.value = Math.round(style.fontSize);
  fontFamilySel.value = style.fontFamily;
  btnBold  .classList.toggle('active', style.bold);
  btnItalic.classList.toggle('active', style.italic);
  textColorInput.value = style.color;
}

function applyStyleToDiv(div) {
  div.style.fontSize   = (style.fontSize * SCALE) + 'px';
  div.style.fontFamily = cssFontFamily(style.fontFamily);
  div.style.fontWeight = style.bold   ? 'bold'   : 'normal';
  div.style.fontStyle  = style.italic ? 'italic' : 'normal';
  div.style.color      = style.color;
}

function finaliseStyle(div) {
  applyStyleToDiv(div);
  // Keep the sampled background so the modified text covers the original
  div.style.background = div.dataset.bgColor || '#ffffff';
}

function resetDivStyle(div) {
  div.style.color      = 'transparent';
  div.style.background = 'transparent';
  div.style.fontFamily = '';
  div.style.fontWeight = '';
  div.style.fontStyle  = '';
  div.style.fontSize   = (parseFloat(div.dataset.pdfFs) * SCALE) + 'px';
}

function cssFontFamily(name) {
  if (name === 'Times-Roman') return 'Georgia, "Times New Roman", serif';
  if (name === 'Courier')     return '"Courier New", Courier, monospace';
  return 'Helvetica, Arial, sans-serif';
}

// ═══════════════════════════════════════════════════════
// 5.  SAVE / DOWNLOAD PDF
// ═══════════════════════════════════════════════════════

document.getElementById('download-btn').addEventListener('click', async () => {
  if (!pdfBytes) return;
  showLoading('Generating PDF…');
  try {
    const bytes = await buildPDF();
    const blob  = new Blob([bytes], { type: 'application/pdf' });
    const url   = URL.createObjectURL(blob);
    const a     = Object.assign(document.createElement('a'), {
      href:     url,
      download: fileName + '_edited.pdf',
    });
    a.click();
    URL.revokeObjectURL(url);
    hideLoading();
  } catch (err) {
    hideLoading();
    console.error(err);
    alert('Error generating PDF:\n' + err.message);
  }
});

async function buildPDF() {
  const { PDFDocument, StandardFonts, rgb } = PDFLib;

  const doc   = await PDFDocument.load(pdfBytes.slice(0));
  const pages = doc.getPages();
  const fonts = await embedFonts(doc, StandardFonts);

  for (const [pageStr, pageEdits] of Object.entries(edits)) {
    const page = pages[parseInt(pageStr) - 1];

    for (const edit of Object.values(pageEdits)) {
      const { x, y, w, origFontSize, newText,
              fontSize, fontFamily, bold, italic, color, bgColor } = edit;

      // 1. Cover rectangle — use the sampled background colour (not hardcoded white)
      const bg    = hexToRgb(bgColor || '#ffffff');
      const rectH = origFontSize * 1.3;
      const rectY = y - origFontSize * 0.25;
      const rectW = Math.max(w, origFontSize * newText.length * 0.6) + 6;

      page.drawRectangle({
        x:      x - 1,
        y:      rectY,
        width:  rectW,
        height: rectH,
        color:  rgb(bg.r / 255, bg.g / 255, bg.b / 255),
      });

      // 2. Draw the new text at the same baseline
      const font = pickFont(fonts, fontFamily, bold, italic);
      const clr  = hexToRgb(color);

      page.drawText(newText, {
        x,
        y,
        size:  fontSize,
        font,
        color: rgb(clr.r / 255, clr.g / 255, clr.b / 255),
      });
    }
  }

  return doc.save();
}

async function embedFonts(doc, SF) {
  return {
    'Helvetica':             await doc.embedFont(SF.Helvetica),
    'Helvetica-Bold':        await doc.embedFont(SF.HelveticaBold),
    'Helvetica-Oblique':     await doc.embedFont(SF.HelveticaOblique),
    'Helvetica-BoldOblique': await doc.embedFont(SF.HelveticaBoldOblique),
    'Times-Roman':           await doc.embedFont(SF.TimesRoman),
    'Times-Bold':            await doc.embedFont(SF.TimesRomanBold),
    'Times-Italic':          await doc.embedFont(SF.TimesRomanItalic),
    'Times-BoldItalic':      await doc.embedFont(SF.TimesRomanBoldItalic),
    'Courier':               await doc.embedFont(SF.Courier),
    'Courier-Bold':          await doc.embedFont(SF.CourierBold),
    'Courier-Oblique':       await doc.embedFont(SF.CourierOblique),
    'Courier-BoldOblique':   await doc.embedFont(SF.CourierBoldOblique),
  };
}

function pickFont(fonts, family, bold, italic) {
  if (family === 'Helvetica') {
    if (bold && italic) return fonts['Helvetica-BoldOblique'];
    if (bold)           return fonts['Helvetica-Bold'];
    if (italic)         return fonts['Helvetica-Oblique'];
    return fonts['Helvetica'];
  }
  if (family === 'Times-Roman') {
    if (bold && italic) return fonts['Times-BoldItalic'];
    if (bold)           return fonts['Times-Bold'];
    if (italic)         return fonts['Times-Italic'];
    return fonts['Times-Roman'];
  }
  if (family === 'Courier') {
    if (bold && italic) return fonts['Courier-BoldOblique'];
    if (bold)           return fonts['Courier-Bold'];
    if (italic)         return fonts['Courier-Oblique'];
    return fonts['Courier'];
  }
  return fonts['Helvetica'];
}

function hexToRgb(hex) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return m
    ? { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) }
    : { r: 0, g: 0, b: 0 };
}

// ═══════════════════════════════════════════════════════
// 6.  LOADING HELPERS
// ═══════════════════════════════════════════════════════

function showLoading(msg) {
  loadingText.textContent = msg || 'Loading…';
  loadingOverlay.classList.remove('hidden');
}
function hideLoading() {
  loadingOverlay.classList.add('hidden');
}
