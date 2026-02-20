"""
Creative Playground — single-creative test harness for rapid V2 iteration.

GET  /v2/playground              → Self-contained HTML page
GET  /v2/playground/params       → Last saved CreativeParameters
POST /v2/playground/params       → Merge partial JSON into saved params
POST /v2/playground/render       → Render one ad type, return PNG or JSON
"""

import json
import logging
import random
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from app.schemas.creative_params import CreativeParameters
from app.services.v2.ad_type_registry import get_registry, get_ad_type
from app.services.v2.copy_generator import generate_copy_from_template, _resolve_variable
from app.services.v2.static_renderer import (
    get_static_renderer,
    ASPECT_RATIO_SIZES,
    _load_template_from_db,
    _resolve_template_variables,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/playground", tags=["playground"])

LAST_PARAMS_PATH = Path(__file__).resolve().parents[2] / "data" / "last_params.json"


# --- Helper ---

def _load_saved_params() -> dict | None:
    """Load last_params.json from disk, return raw dict or None."""
    try:
        if LAST_PARAMS_PATH.exists():
            return json.loads(LAST_PARAMS_PATH.read_text())
    except Exception as e:
        logger.warning(f"Failed to load saved params: {e}")
    return None


def _save_params(data: dict) -> None:
    LAST_PARAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_PARAMS_PATH.write_text(json.dumps(data, indent=2))


# --- Endpoints ---

@router.get("/params")
async def get_saved_params():
    """Return last saved CreativeParameters (from most recent analysis)."""
    data = _load_saved_params()
    if not data:
        raise HTTPException(status_code=404, detail="No saved params — run a V2 analysis first")
    return data


@router.post("/params")
async def update_saved_params(request: Request):
    """Merge partial JSON into saved params (for quick edits)."""
    body = await request.json()
    existing = _load_saved_params() or {}
    existing.update(body)
    _save_params(existing)
    return existing


class PlaygroundRenderRequest(BaseModel):
    ad_type_id: str
    aspect_ratio: str = "1:1"
    params: dict | None = None  # override params; if None, load from disk
    template_json: dict | None = None  # override template; if None, load from DB


@router.post("/render")
async def render_single(body: PlaygroundRenderRequest, request: Request):
    """
    Render a single ad type. Returns PNG by default, or JSON with copy + base64
    image if Accept: application/json.
    """
    # Load params
    if body.params:
        params_dict = body.params
    else:
        params_dict = _load_saved_params()
        if not params_dict:
            raise HTTPException(status_code=400, detail="No params provided and no saved params on disk")

    try:
        params = CreativeParameters(**params_dict)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid params: {e}")

    # Resolve ad type
    ad_type = get_ad_type(body.ad_type_id)
    if not ad_type:
        raise HTTPException(status_code=404, detail=f"Unknown ad type: {body.ad_type_id}")

    # Resolve hook text
    hook_text = _resolve_hook(ad_type, params)

    # Generate copy
    copy_data = generate_copy_from_template(ad_type, params)

    # Load or use provided template
    canvas_json = body.template_json
    if not canvas_json:
        canvas_json = await _load_template_from_db(body.ad_type_id, body.aspect_ratio)

    w, h = ASPECT_RATIO_SIZES.get(body.aspect_ratio, (1080, 1080))

    start = time.time()

    if canvas_json:
        # Template path: resolve variables and render via Node.js
        populated = _resolve_template_variables(canvas_json, params, hook_text)
        renderer = get_static_renderer()
        try:
            img_bytes = await renderer.render_from_template(
                canvas_json=populated, params=params, width=w, height=h
            )
        except Exception:
            # Fallback to full render_ad which includes Pillow fallback
            img_bytes = await renderer.render_ad(ad_type, params, body.aspect_ratio, hook_text)
    else:
        # No template — use Pillow fallback
        renderer = get_static_renderer()
        img_bytes = await renderer.render_ad(ad_type, params, body.aspect_ratio, hook_text)

    render_ms = int((time.time() - start) * 1000)

    # Return JSON or PNG based on Accept header
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        import base64
        return {
            "image_base64": base64.b64encode(img_bytes).decode(),
            "copy": dict(copy_data),
            "render_time_ms": render_ms,
            "ad_type_id": body.ad_type_id,
            "aspect_ratio": body.aspect_ratio,
            "template_found": canvas_json is not None,
        }

    return Response(
        content=img_bytes,
        media_type="image/png",
        headers={
            "X-Render-Time-Ms": str(render_ms),
            "X-Ad-Type": body.ad_type_id,
        },
    )


class ImageEditRequest(BaseModel):
    prompt: str
    overlay_text: str | None = None
    overlay_position: str = "bottom-left"


@router.post("/edit-image")
async def edit_image_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form(...),
):
    """Edit an uploaded image using Gemini AI and return the result."""
    import base64

    image_bytes = await file.read()
    mime = file.content_type or "image/png"

    try:
        from app.services.v2.image_editor import edit_image
        edited = await edit_image(image_bytes, prompt, mime)
    except Exception as e:
        logger.error(f"Image edit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "image_base64": base64.b64encode(edited).decode(),
        "mime_type": "image/png",
    }


class ShowcaseRenderRequest(BaseModel):
    image_base64: str
    overlay_text: str | None = None
    overlay_position: str = "bottom-left"


@router.post("/render-showcase")
async def render_showcase_endpoint(body: ShowcaseRenderRequest):
    """Render product showcase: image + optional text overlay."""
    import base64

    # Write image to temp file for the renderer
    import tempfile
    img_bytes = base64.b64decode(body.image_base64)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(img_bytes)
        tmp_path = f.name

    try:
        from app.services.v2.social_templates.product_showcase import (
            ProductShowcaseParams,
            render_product_showcase,
        )
        params = ProductShowcaseParams(
            product_image_url=f"file://{tmp_path}",
            overlay_text=body.overlay_text,
            overlay_position=body.overlay_position,
        )
        result = await render_product_showcase(params)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return {
        "image_base64": base64.b64encode(result).decode(),
    }


def _resolve_hook(ad_type, params: CreativeParameters) -> str | None:
    """Pick a random hook from hook_templates and resolve variables."""
    if not ad_type.hook_templates:
        return None
    variants = list(ad_type.hook_templates.keys())
    if params.business_type == "saas":
        saas_keys = [k for k in variants if k.startswith("saas_")]
        if saas_keys:
            variants = saas_keys
    key = random.choice(variants)
    hooks = ad_type.hook_templates[key]
    if not hooks:
        return None
    hook = random.choice(hooks)
    return _resolve_variable(hook, params)


# --- Self-contained HTML playground ---

@router.get("", response_class=HTMLResponse)
async def playground_page():
    """Serve the playground HTML page — zero build step, fully self-contained."""
    return HTMLResponse(content=PLAYGROUND_HTML)


PLAYGROUND_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V2 Creative Playground</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --text: #e4e4e7;
    --text-muted: #8b8d98;
    --accent: #38BDF8;
    --accent-dark: #0EA5E9;
    --success: #34d399;
    --error: #f87171;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }
  header {
    padding: 16px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 16px;
  }
  header h1 {
    font-size: 18px;
    font-weight: 600;
    color: var(--accent);
  }
  header .badge {
    font-size: 11px;
    background: var(--accent-dark);
    color: white;
    padding: 2px 8px;
    border-radius: 10px;
  }
  .main {
    display: grid;
    grid-template-columns: 280px 1fr 320px;
    grid-template-rows: 1fr auto;
    height: calc(100vh - 57px);
  }
  /* Left panel */
  .panel-left {
    padding: 20px;
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 16px;
    overflow-y: auto;
  }
  .field-group { display: flex; flex-direction: column; gap: 6px; }
  .field-group label {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  select, input[type="text"] {
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    outline: none;
  }
  select:focus, input:focus { border-color: var(--accent); }
  .ratio-group { display: flex; gap: 6px; flex-wrap: wrap; }
  .ratio-btn {
    padding: 6px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg);
    color: var(--text-muted);
    cursor: pointer;
    font-size: 13px;
    transition: all 0.15s;
  }
  .ratio-btn.active {
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(56,189,248,0.1);
  }
  .btn-render {
    width: 100%;
    padding: 12px;
    background: var(--accent);
    color: #000;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
  }
  .btn-render:hover { background: var(--accent-dark); color: #fff; }
  .btn-render:disabled { opacity: 0.5; cursor: not-allowed; }
  .render-info {
    font-size: 12px;
    color: var(--text-muted);
    text-align: center;
  }
  .render-info .time { color: var(--success); font-weight: 600; }
  /* Center panel */
  .panel-center {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background: var(--bg);
    overflow: auto;
    position: relative;
  }
  .panel-center img {
    max-width: 100%;
    max-height: 100%;
    border-radius: 8px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  }
  .placeholder {
    color: var(--text-muted);
    font-size: 14px;
    text-align: center;
  }
  .placeholder .icon { font-size: 48px; opacity: 0.3; margin-bottom: 12px; }
  .spinner {
    display: none;
    width: 32px;
    height: 32px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
  @keyframes spin { to { transform: translate(-50%, -50%) rotate(360deg); } }
  /* Right panel */
  .panel-right {
    padding: 20px;
    border-left: 1px solid var(--border);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .copy-section h3 {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
    margin-bottom: 6px;
  }
  .copy-value {
    font-size: 14px;
    line-height: 1.5;
    padding: 10px 12px;
    background: var(--bg);
    border-radius: 6px;
    border: 1px solid var(--border);
    white-space: pre-wrap;
    word-break: break-word;
  }
  /* Bottom panels */
  .panel-bottom {
    grid-column: 1 / -1;
    border-top: 1px solid var(--border);
  }
  .collapsible-header {
    padding: 10px 20px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    user-select: none;
  }
  .collapsible-header:hover { color: var(--text); }
  .collapsible-header .arrow { transition: transform 0.2s; }
  .collapsible-header.open .arrow { transform: rotate(90deg); }
  .collapsible-body {
    display: none;
    padding: 0 20px 16px;
  }
  .collapsible-body.open { display: flex; gap: 16px; }
  textarea {
    width: 100%;
    min-height: 200px;
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 12px;
    padding: 12px;
    border-radius: 6px;
    resize: vertical;
    outline: none;
    flex: 1;
  }
  textarea:focus { border-color: var(--accent); }
  .btn-small {
    padding: 6px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
  }
  .btn-small:hover { border-color: var(--accent); color: var(--accent); }
  .toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 13px;
    z-index: 100;
    opacity: 0;
    transition: opacity 0.3s;
  }
  .toast.show { opacity: 1; }
  .toast.success { background: #065f46; color: #34d399; }
  .toast.error { background: #7f1d1d; color: #f87171; }
</style>
</head>
<body>

<header>
  <h1>V2 Creative Playground</h1>
  <span class="badge">DEV</span>
</header>

<div class="main">
  <!-- Left Panel: Controls -->
  <div class="panel-left">
    <div class="field-group">
      <label>Analyze URL</label>
      <div style="display:flex; gap:6px;">
        <input type="text" id="urlInput" placeholder="https://example.com" style="flex:1; min-width:0;">
        <button class="btn-small" id="analyzeBtn" onclick="doAnalyze()" style="white-space:nowrap;">Analyze</button>
      </div>
      <div id="analyzeStatus" style="font-size:11px; color:var(--text-muted);"></div>
    </div>

    <hr style="border-color: var(--border);">

    <div class="field-group">
      <label>Ad Type</label>
      <select id="adTypeSelect"><option value="">Loading...</option></select>
    </div>

    <div class="field-group">
      <label>Aspect Ratio</label>
      <div class="ratio-group" id="ratioGroup">
        <button class="ratio-btn active" data-ratio="1:1">1:1</button>
        <button class="ratio-btn" data-ratio="9:16">9:16</button>
        <button class="ratio-btn" data-ratio="1.91:1">1.91:1</button>
        <button class="ratio-btn" data-ratio="4:5">4:5</button>
      </div>
    </div>

    <button class="btn-render" id="renderBtn" onclick="doRender()">Render</button>

    <div class="render-info" id="renderInfo"></div>

    <hr style="border-color: var(--border);">

    <div class="field-group" style="font-size:12px; color:var(--text-muted);">
      <strong>Keyboard Shortcuts</strong>
      <div>Ctrl+Enter &mdash; Render</div>
      <div>1/2/3/4 &mdash; Switch ratio</div>
    </div>
  </div>

  <!-- Center Panel: Image Preview -->
  <div class="panel-center" id="previewPanel">
    <div class="placeholder" id="placeholderMsg">
      <div class="icon">&#x1f3a8;</div>
      Select an ad type and click Render
    </div>
    <div class="spinner" id="spinner"></div>
  </div>

  <!-- Right Panel: Copy -->
  <div class="panel-right" id="copyPanel">
    <div class="copy-section">
      <h3>Primary Text</h3>
      <div class="copy-value" id="copyPrimary">&mdash;</div>
    </div>
    <div class="copy-section">
      <h3>Headline</h3>
      <div class="copy-value" id="copyHeadline">&mdash;</div>
    </div>
    <div class="copy-section">
      <h3>Description</h3>
      <div class="copy-value" id="copyDescription">&mdash;</div>
    </div>
    <div class="copy-section">
      <h3>CTA Type</h3>
      <div class="copy-value" id="copyCta">&mdash;</div>
    </div>
  </div>

  <!-- Bottom: Collapsible editors -->
  <div class="panel-bottom">
    <!-- Params editor -->
    <div class="collapsible-header" onclick="toggleCollapsible(this)">
      <span class="arrow">&#9654;</span> Params JSON Editor
    </div>
    <div class="collapsible-body">
      <textarea id="paramsEditor" placeholder="Loading params..."></textarea>
      <div style="display:flex; flex-direction:column; gap:8px; min-width:80px;">
        <button class="btn-small" onclick="saveParams()">Save</button>
        <button class="btn-small" onclick="reloadParams()">Reload</button>
      </div>
    </div>

    <!-- Template viewer -->
    <div class="collapsible-header" onclick="toggleCollapsible(this)">
      <span class="arrow">&#9654;</span> Template JSON (read-only, from DB)
    </div>
    <div class="collapsible-body">
      <textarea id="templateViewer" readonly placeholder="Select an ad type to load its template..."></textarea>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const API = '';
let adTypes = [];
let currentRatio = '1:1';
let rendering = false;
let analyzing = false;

async function init() {
  await Promise.all([loadAdTypes(), loadParams()]);
  // Allow pressing Enter in URL input to trigger analyze
  document.getElementById('urlInput').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') { e.preventDefault(); doAnalyze(); }
  });
}

async function doAnalyze() {
  var url = document.getElementById('urlInput').value.trim();
  if (!url) { toast('Enter a URL first', 'error'); return; }
  if (analyzing) return;

  analyzing = true;
  var btn = document.getElementById('analyzeBtn');
  var status = document.getElementById('analyzeStatus');
  btn.disabled = true;
  btn.textContent = '...';
  status.textContent = 'Starting analysis...';

  try {
    // Start async job
    var res = await fetch(API + '/v2/analyze/async', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url })
    });
    if (!res.ok) {
      var err = await res.json();
      throw new Error(err.detail || res.statusText);
    }
    var job = await res.json();
    status.textContent = 'Analyzing... (job ' + job.job_id + ')';

    // Poll for completion
    var maxPolls = 60; // 60 x 2s = 2 min max
    for (var i = 0; i < maxPolls; i++) {
      await new Promise(function(r) { setTimeout(r, 2000); });
      var pollRes = await fetch(API + '/jobs/' + job.job_id);
      var pollData = await pollRes.json();

      if (pollData.status === 'complete') {
        // Load the saved params (v2 analyze persists them)
        await loadParams();
        status.textContent = 'Done! Params loaded.';
        toast('Analysis complete \u2014 params loaded', 'success');
        return;
      } else if (pollData.status === 'failed') {
        throw new Error(pollData.error || 'Analysis failed');
      }
      status.textContent = 'Analyzing... (' + ((i + 1) * 2) + 's)';
    }
    throw new Error('Analysis timed out after 2 minutes');
  } catch (e) {
    status.textContent = 'Failed: ' + e.message;
    toast('Analysis failed: ' + e.message, 'error');
  } finally {
    analyzing = false;
    btn.disabled = false;
    btn.textContent = 'Analyze';
  }
}

async function loadAdTypes() {
  try {
    const res = await fetch(API + '/v2/ad-types');
    adTypes = await res.json();
    const sel = document.getElementById('adTypeSelect');
    // Clear and rebuild
    while (sel.firstChild) sel.removeChild(sel.firstChild);
    const defaultOpt = document.createElement('option');
    defaultOpt.value = '';
    defaultOpt.textContent = '-- select --';
    sel.appendChild(defaultOpt);

    const grouped = {};
    adTypes.forEach(function(t) {
      if (!grouped[t.strategy]) grouped[t.strategy] = [];
      grouped[t.strategy].push(t);
    });
    Object.keys(grouped).forEach(function(strategy) {
      const og = document.createElement('optgroup');
      og.label = strategy.replace('_', ' ').replace(/\\b\\w/g, function(c) { return c.toUpperCase(); });
      grouped[strategy].forEach(function(t) {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = t.name + ' (' + t.format + ')';
        og.appendChild(opt);
      });
      sel.appendChild(og);
    });
    sel.addEventListener('change', onAdTypeChange);
  } catch (e) {
    toast('Failed to load ad types: ' + e.message, 'error');
  }
}

async function loadParams() {
  try {
    const res = await fetch(API + '/v2/playground/params');
    if (res.ok) {
      const data = await res.json();
      document.getElementById('paramsEditor').value = JSON.stringify(data, null, 2);
    } else {
      document.getElementById('paramsEditor').value = '{}\\n// No saved params yet. Run a V2 analysis first.';
    }
  } catch (e) {
    document.getElementById('paramsEditor').value = '// Failed to load params';
  }
}

async function onAdTypeChange() {
  const adTypeId = document.getElementById('adTypeSelect').value;
  if (!adTypeId) return;
  await loadTemplate(adTypeId, currentRatio);
}

async function loadTemplate(adTypeId, ratio) {
  try {
    const res = await fetch(API + '/v2/templates/' + adTypeId);
    if (res.ok) {
      const templates = await res.json();
      const match = templates.find(function(t) { return t.aspect_ratio === ratio; }) || templates[0];
      if (match) {
        document.getElementById('templateViewer').value = JSON.stringify(match.canvas_json, null, 2);
      } else {
        document.getElementById('templateViewer').value = '// No template in DB for this type/ratio';
      }
    } else {
      document.getElementById('templateViewer').value = '// No template found (will use Pillow fallback)';
    }
  } catch (e) {
    document.getElementById('templateViewer').value = '// Failed to load template';
  }
}

async function doRender() {
  const adTypeId = document.getElementById('adTypeSelect').value;
  if (!adTypeId) { toast('Select an ad type first', 'error'); return; }
  if (rendering) return;

  rendering = true;
  var btn = document.getElementById('renderBtn');
  btn.disabled = true;
  btn.textContent = 'Rendering...';
  document.getElementById('spinner').style.display = 'block';
  document.getElementById('placeholderMsg').style.display = 'none';

  var params = null;
  try {
    var raw = document.getElementById('paramsEditor').value;
    params = JSON.parse(raw);
  } catch (e) {
    toast('Invalid params JSON: ' + e.message, 'error');
    rendering = false;
    btn.disabled = false;
    btn.textContent = 'Render';
    document.getElementById('spinner').style.display = 'none';
    return;
  }

  var payload = {
    ad_type_id: adTypeId,
    aspect_ratio: currentRatio,
    params: params
  };

  try {
    var res = await fetch(API + '/v2/playground/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      var err = await res.json();
      throw new Error(err.detail || res.statusText);
    }
    var data = await res.json();

    // Show image
    var preview = document.getElementById('previewPanel');
    var img = preview.querySelector('img');
    if (!img) {
      img = document.createElement('img');
      preview.appendChild(img);
    }
    img.src = 'data:image/png;base64,' + data.image_base64;

    // Show copy using textContent (safe)
    document.getElementById('copyPrimary').textContent = data.copy.primary_text || '\u2014';
    document.getElementById('copyHeadline').textContent = data.copy.headline || '\u2014';
    document.getElementById('copyDescription').textContent = data.copy.description || '\u2014';
    document.getElementById('copyCta').textContent = data.copy.cta_type || '\u2014';

    // Render info using textContent (safe)
    var tpl = data.template_found ? 'Fabric.js' : 'Pillow fallback';
    var infoEl = document.getElementById('renderInfo');
    infoEl.textContent = '';
    var timeSpan = document.createElement('span');
    timeSpan.className = 'time';
    timeSpan.textContent = data.render_time_ms + 'ms';
    infoEl.appendChild(timeSpan);
    infoEl.appendChild(document.createTextNode(' \u00b7 ' + tpl + ' \u00b7 ' + data.aspect_ratio));

    toast('Rendered in ' + data.render_time_ms + 'ms', 'success');
  } catch (e) {
    toast('Render failed: ' + e.message, 'error');
  } finally {
    rendering = false;
    btn.disabled = false;
    btn.textContent = 'Render';
    document.getElementById('spinner').style.display = 'none';
  }
}

async function saveParams() {
  try {
    var raw = document.getElementById('paramsEditor').value;
    var data = JSON.parse(raw);
    var res = await fetch(API + '/v2/playground/params', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (res.ok) {
      toast('Params saved', 'success');
    } else {
      toast('Failed to save params', 'error');
    }
  } catch (e) {
    toast('Invalid JSON: ' + e.message, 'error');
  }
}

async function reloadParams() {
  await loadParams();
  toast('Params reloaded', 'success');
}

function toggleCollapsible(header) {
  header.classList.toggle('open');
  var body = header.nextElementSibling;
  body.classList.toggle('open');
}

document.getElementById('ratioGroup').addEventListener('click', function(e) {
  if (!e.target.classList.contains('ratio-btn')) return;
  document.querySelectorAll('.ratio-btn').forEach(function(b) { b.classList.remove('active'); });
  e.target.classList.add('active');
  currentRatio = e.target.dataset.ratio;
  var adTypeId = document.getElementById('adTypeSelect').value;
  if (adTypeId) loadTemplate(adTypeId, currentRatio);
});

document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    doRender();
  }
  if (['INPUT', 'TEXTAREA', 'SELECT'].indexOf(document.activeElement && document.activeElement.tagName) !== -1) return;
  var ratioMap = { '1': '1:1', '2': '9:16', '3': '1.91:1', '4': '4:5' };
  if (ratioMap[e.key]) {
    currentRatio = ratioMap[e.key];
    document.querySelectorAll('.ratio-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.ratio === currentRatio);
    });
    var adTypeId = document.getElementById('adTypeSelect').value;
    if (adTypeId) loadTemplate(adTypeId, currentRatio);
  }
});

function toast(msg, type) {
  type = type || 'success';
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast ' + type + ' show';
  setTimeout(function() { t.classList.remove('show'); }, 3000);
}

init();
</script>
</body>
</html>
"""
