const $ = id => document.getElementById(id);
let selectedImageDataUrl = null;
let selectedImage = null;

$('priority').addEventListener('input', () => { $('pv').textContent = $('priority').value; });

function syncModelFields() {
  const isYolo = $('model').value === 'yolo';
  $('textInput').hidden = isYolo;
  $('imageInput').hidden = !isYolo;
  $('text').required = !isYolo;
  $('imageFile').required = isYolo;
}
$('model').addEventListener('change', syncModelFields);
syncModelFields();

$('imageFile').addEventListener('change', () => {
  const file = $('imageFile').files?.[0];
  selectedImageDataUrl = null;
  selectedImage = null;
  $('imagePreviewWrap').hidden = true;
  if (!file) return;
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    $('status').textContent = 'Choose a JPG, PNG, or WebP image.';
    $('imageFile').value = '';
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    $('status').textContent = 'Image must be 10 MB or smaller.';
    $('imageFile').value = '';
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    selectedImageDataUrl = String(reader.result);
    selectedImage = new Image();
    selectedImage.onload = () => {
      $('imagePreview').src = selectedImageDataUrl;
      $('imagePreviewWrap').hidden = false;
    };
    selectedImage.src = selectedImageDataUrl;
  };
  reader.readAsDataURL(file);
});

$('clearImage').addEventListener('click', () => {
  $('imageFile').value = '';
  $('imagePreview').removeAttribute('src');
  $('imagePreviewWrap').hidden = true;
  selectedImageDataUrl = null;
  selectedImage = null;
});

$('check').addEventListener('click', async () => {
  const base = $('base').value.trim().replace(/\/+$/, '');
  $('check').disabled = true;
  $('check').textContent = 'Checking…';
  try {
    const [h, m] = await Promise.all([fetch(base + '/health'), fetch(base + '/models')]);
    if (!h.ok || !m.ok) throw Error('HTTP ' + h.status + '/' + m.status);
    const health = await h.json();
    const models = await m.json();
    $('health').textContent = health.status || 'Healthy';
    $('health').className = 'good';
    const list = Array.isArray(models) ? models : (models.models || models.data || []);
    $('count').textContent = (list.length || health.model_registry?.registered || 0) + ' registered';
    $('count').className = 'good';
    $('healthMessage').textContent = 'Gateway reachable. ' + JSON.stringify(health);
  } catch (e) {
    $('health').textContent = 'Unavailable';
    $('count').textContent = 'Not reached';
    $('healthMessage').textContent = 'Could not reach ' + base + '. Confirm the gateway is running and CORS allows this website. ' + e.message;
  } finally {
    $('check').disabled = false;
    $('check').textContent = 'Check local API status ↗';
  }
});

function showPlaceholder(title, message, glyph = '⌘') {
  $('placeholder').hidden = false;
  $('placeholder').innerHTML = `<div class="glyph">${glyph}</div><b>${title}</b><p>${message}</p>`;
}

function renderDetections(body) {
  const result = body?.result ?? body;
  const detections = result?.detections;
  $('detectionSummary').hidden = true;
  $('annotatedWrap').hidden = true;
  if (!Array.isArray(detections)) return;
  $('detectionSummary').hidden = false;
  $('detectionSummary').innerHTML = `<b>${detections.length} detection${detections.length === 1 ? '' : 's'} returned</b>` +
    (detections.length ? '<ul>' + detections.map(d => {
      const label = String(d.label ?? d.class_name ?? d.class ?? 'object');
      const confidence = Number(d.confidence);
      const confidenceText = Number.isFinite(confidence) ? ` · ${(confidence * 100).toFixed(1)}%` : '';
      return `<li><span>${escapeHtml(label)}</span><strong>${confidenceText}</strong></li>`;
    }).join('') + '</ul>' : '<p>No objects detected in this image.</p>');
  if (!selectedImage || !detections.some(d => Array.isArray(d.bbox) && d.bbox.length >= 4)) return;
  const canvas = $('annotatedCanvas');
  const ctx = canvas.getContext('2d');
  canvas.width = selectedImage.naturalWidth;
  canvas.height = selectedImage.naturalHeight;
  ctx.drawImage(selectedImage, 0, 0, canvas.width, canvas.height);
  const scale = Math.max(1, canvas.width / 500);
  ctx.lineWidth = 2 * scale;
  ctx.font = `${Math.max(12, 12 * scale)}px sans-serif`;
  detections.forEach(d => {
    if (!Array.isArray(d.bbox) || d.bbox.length < 4) return;
    const [x1, y1, x2, y2] = d.bbox.map(Number);
    if (![x1, y1, x2, y2].every(Number.isFinite)) return;
    ctx.strokeStyle = '#19d3a2';
    ctx.fillStyle = '#19d3a2';
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    const label = String(d.label ?? d.class_name ?? d.class ?? 'object');
    const conf = Number(d.confidence);
    const tag = Number.isFinite(conf) ? `${label} ${(conf * 100).toFixed(0)}%` : label;
    const textWidth = ctx.measureText(tag).width + 10;
    const tagY = Math.max(0, y1 - 22 * scale);
    ctx.fillRect(x1, tagY, textWidth, 22 * scale);
    ctx.fillStyle = '#07121d';
    ctx.fillText(tag, x1 + 5, tagY + 15 * scale);
  });
  $('annotatedWrap').hidden = false;
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}

$('form').addEventListener('submit', async e => {
  e.preventDefault();
  const base = $('base').value.trim().replace(/\/+$/, '');
  const model = $('model').value;
  const text = $('text').value.trim();
  if (model === 'yolo' && !selectedImageDataUrl) {
    $('status').textContent = 'Choose an image before running YOLO.';
    $('imageFile').focus();
    return;
  }
  if (model !== 'yolo' && !text) {
    $('status').textContent = 'Enter some text first.';
    $('text').focus();
    return;
  }
  const payload = { model, priority: Number($('priority').value) };
  if (model === 'yolo') payload.image_base64 = selectedImageDataUrl.split(',')[1];
  else payload.text = text;

  $('submit').disabled = true;
  $('submit').textContent = 'Running inference…';
  showPlaceholder('Request in progress…', 'Waiting for the local inference worker.');
  $('resultArea').hidden = true;
  $('time').textContent = 'RUNNING';
  $('status').textContent = 'Request in progress';
  const start = performance.now();
  try {
    const res = await fetch(base + '/infer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const body = await res.json();
    $('time').textContent = Math.round(performance.now() - start) + ' MS';
    $('placeholder').hidden = true;
    $('resultArea').hidden = false;
    $('result').textContent = JSON.stringify(body, null, 2);
    $('status').textContent = res.ok ? 'Inference completed' : 'Request failed · HTTP ' + res.status;
    if (res.ok && model === 'yolo') renderDetections(body);
    else {
      $('detectionSummary').hidden = true;
      $('annotatedWrap').hidden = true;
    }
  } catch (err) {
    $('time').textContent = 'ERROR';
    showPlaceholder('Could not reach the API', 'Check the API URL, running gateway, network access, and browser CORS configuration.', '!');
    $('status').textContent = err.message;
  } finally {
    $('submit').disabled = false;
    $('submit').textContent = 'Run inference ↗';
  }
});
