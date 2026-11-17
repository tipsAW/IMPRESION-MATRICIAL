# -*- coding: utf-8 -*-
"""
Servicio Web para Unir Comprobantes 2 por Hoja A4 / Carta.
Permite compartirlo en la red local para que cualquier usuario pueda
procesar archivos individuales o un solo PDF de múltiples páginas (ej. 50+ páginas).
"""

import base64
import os
import socket
from typing import List, Optional
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, Response, JSONResponse
import uvicorn

from procesador import procesar_comprobantes, obtener_preview_png

app = FastAPI(title="Unificador de Comprobantes 2x1", version="2.0.0")


def obtener_ips_locales():
    """Detecta las direcciones IP locales para mostrar en pantalla."""
    ips = []
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and not ip.startswith("169.254"):
                ips.append(ip)
    except Exception:
        pass
    if not ips:
        ips.append("127.0.0.1")
    return ips


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Unificador de Comprobantes 2x1 – A4 / Matricial</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --text: #1e293b;
      --text-muted: #64748b;
      --success: #16a34a;
      --radius: 12px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
    body { background-color: var(--bg); color: var(--text); min-height: 100vh; padding: 24px 16px; }
    .container { max-width: 960px; margin: 0 auto; }
    
    header {
      background: var(--card-bg);
      padding: 24px 32px;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }
    .brand h1 { font-size: 1.4rem; font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 8px; }
    .brand p { font-size: 0.88rem; color: var(--text-muted); margin-top: 4px; }
    .badge-ip {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #1e40af;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 600;
    }

    .grid { display: grid; grid-template-columns: 1fr; gap: 24px; }
    @media(min-width: 768px) { .grid { grid-template-columns: 1.15fr 0.85fr; } }

    .card {
      background: var(--card-bg);
      padding: 24px;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .card-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

    /* Dropzone */
    .dropzone {
      border: 2px dashed #93c5fd;
      border-radius: var(--radius);
      padding: 36px 20px;
      text-align: center;
      background: #f8fbff;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .dropzone:hover, .dropzone.dragover {
      border-color: var(--primary);
      background: #eff6ff;
      transform: translateY(-1px);
    }
    .dropzone svg { width: 44px; height: 44px; color: var(--primary); margin-bottom: 12px; }
    .dropzone p { font-size: 0.95rem; font-weight: 500; color: #334155; }
    .dropzone span { font-size: 0.8rem; color: var(--text-muted); display: block; margin-top: 4px; }
    #fileInput { display: none; }

    /* File List */
    .file-list { margin-top: 16px; max-height: 180px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
    .file-item {
      display: flex; justify-content: space-between; align-items: center;
      padding: 8px 12px; background: #f1f5f9; border-radius: 8px; font-size: 0.85rem;
    }
    .file-name { font-weight: 500; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 320px; }
    .file-remove { color: #ef4444; cursor: pointer; font-size: 1rem; border: none; background: none; padding: 0 4px; }

    /* Options */
    .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
    .form-group label { display: block; font-size: 0.8rem; font-weight: 600; color: #475569; margin-bottom: 6px; }
    .form-control {
      width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px;
      font-size: 0.9rem; background: white; color: var(--text);
    }
    .checkbox-group { display: flex; align-items: center; gap: 8px; margin-top: 16px; font-size: 0.85rem; color: #334155; }
    .checkbox-group input { width: 16px; height: 16px; accent-color: var(--primary); }

    /* Stats */
    .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }
    .stat-box { background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 12px; text-align: center; }
    .stat-val { font-size: 1.4rem; font-weight: 700; color: var(--primary); }
    .stat-label { font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; margin-top: 4px; font-weight: 600; }

    /* Buttons */
    .btn-group { display: flex; flex-direction: column; gap: 10px; margin-top: 20px; }
    .btn {
      display: inline-flex; justify-content: center; align-items: center; gap: 8px;
      padding: 12px 20px; border-radius: 8px; font-size: 0.95rem; font-weight: 600;
      border: none; cursor: pointer; transition: all 0.2s ease; text-decoration: none;
    }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover:not(:disabled) { background: var(--primary-hover); }
    .btn-secondary { background: #e2e8f0; color: #334155; }
    .btn-secondary:hover:not(:disabled) { background: #cbd5e1; }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }

    /* Preview section */
    .preview-container {
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      min-height: 400px; background: #f1f5f9; border-radius: var(--radius); border: 1px dashed #cbd5e1;
      padding: 16px; text-align: center;
    }
    .preview-img { max-width: 100%; max-height: 480px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 4px; background: white; }
    .preview-placeholder { color: var(--text-muted); font-size: 0.9rem; }
    .preview-placeholder svg { width: 48px; height: 48px; opacity: 0.4; margin-bottom: 8px; }

    /* Spinner */
    .spinner {
      border: 3px solid rgba(255,255,255,0.3); border-radius: 50%;
      border-top: 3px solid white; width: 18px; height: 18px; animation: spin 0.8s linear infinite; display: none;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
  </style>
</head>
<body>

<div class="container">
  <header>
    <div class="brand">
      <h1>📄 Unificador de Comprobantes 2x1</h1>
      <p>Pega 2 comprobantes por hoja A4 / Carta – Ahorra papel y espacio</p>
    </div>
    <div class="badge-ip" id="badgeShare">
      🌐 Compartir enlace: <strong id="shareUrl">...</strong>
    </div>
  </header>

  <div class="grid">
    <!-- Columna Izquierda: Carga y Opciones -->
    <div class="card">
      <div class="card-title">📤 1. Cargar comprobantes</div>
      
      <div class="dropzone" id="dropzone" onclick="document.getElementById('fileInput').click()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
        </svg>
        <p>Arrastra aquí tu PDF (de 1 o 50+ páginas) o múltiples PDFs</p>
        <span>Compatible con archivos individuales o lotes completos</span>
      </div>
      <input type="file" id="fileInput" multiple accept=".pdf" onchange="manejarArchivos(this.files)">

      <div class="file-list" id="fileList"></div>

      <div class="card-title" style="margin-top: 24px;">⚙️ 2. Opciones de hoja</div>
      <div class="options-grid">
        <div class="form-group">
          <label>Tamaño de Papel</label>
          <select class="form-control" id="tamanoPapel" onchange="actualizarPrevisualizacion()">
            <option value="A4" selected>A4 (210 × 297 mm)</option>
            <option value="Carta">Carta / Letter (8.5 × 11 in)</option>
          </select>
        </div>
        <div class="form-group">
          <label>Margen Extra de Recorte</label>
          <select class="form-control" id="margenRecorte">
            <option value="6" selected>Normal (6 pt)</option>
            <option value="12">Amplio (12 pt)</option>
            <option value="0">Sin margen extra (0 pt)</option>
          </select>
        </div>
      </div>

      <div class="checkbox-group">
        <input type="checkbox" id="lineaCorte" checked onchange="actualizarPrevisualizacion()">
        <label for="lineaCorte">Dibujar línea punteada divisoria central (corte / doblez)</label>
      </div>

      <div class="stats-row" id="statsRow" style="display: none;">
        <div class="stat-box">
          <div class="stat-val" id="statComprobantes">0</div>
          <div class="stat-label">Comprobantes</div>
        </div>
        <div class="stat-box">
          <div class="stat-val" id="statHojas">0</div>
          <div class="stat-label">Hojas Finales</div>
        </div>
        <div class="stat-box">
          <div class="stat-val" id="statAhorro" style="color: var(--success);">50%</div>
          <div class="stat-label">Ahorro Papel</div>
        </div>
      </div>

      <div class="btn-group">
        <button class="btn btn-primary" id="btnDescargar" onclick="procesarYDescargar(false)" disabled>
          <div class="spinner" id="spinnerDescargar"></div>
          <span id="btnTextDescargar">💾 Descargar PDF Combinado</span>
        </button>
        <button class="btn btn-secondary" id="btnImprimir" onclick="procesarYDescargar(true)" disabled>
          🖨️ Abrir para Imprimir (Ctrl+P)
        </button>
        <button class="btn" style="background: transparent; color: #64748b; font-size: 0.85rem;" onclick="limpiarTodo()">
          🗑 Limpiar lista
        </button>
      </div>
    </div>

    <!-- Columna Derecha: Previsualización -->
    <div class="card">
      <div class="card-title">👁 Vista Previa (Hoja 1)</div>
      <div class="preview-container" id="previewContainer">
        <div class="preview-placeholder" id="previewPlaceholder">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          <p>Carga tus archivos para ver cómo quedarán distribuidos 2 en cada hoja.</p>
        </div>
        <img id="previewImage" class="preview-img" style="display: none;" alt="Vista previa de hoja 1">
      </div>
    </div>
  </div>
</div>

<script>
  let listaArchivos = [];

  // Mostrar la URL actual de forma dinámica (local o Render)
  document.addEventListener('DOMContentLoaded', () => {
    const shareEl = document.getElementById('shareUrl');
    if (shareEl) {
      shareEl.innerText = window.location.origin;
    }
  });

  const dropzone = document.getElementById('dropzone');
  ['dragenter', 'dragover'].forEach(name => {
    dropzone.addEventListener(name, (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
  });
  ['dragleave', 'drop'].forEach(name => {
    dropzone.addEventListener(name, (e) => { e.preventDefault(); dropzone.classList.remove('dragover'); });
  });
  dropzone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files.length) {
      manejarArchivos(e.dataTransfer.files);
    }
  });

  function manejarArchivos(archivos) {
    for (let f of archivos) {
      if (f.name.toLowerCase().endsWith('.pdf')) {
        listaArchivos.push(f);
      }
    }
    actualizarListaUI();
    actualizarPrevisualizacion();
  }

  function actualizarListaUI() {
    const contenedor = document.getElementById('fileList');
    contenedor.innerHTML = '';
    listaArchivos.forEach((f, idx) => {
      const item = document.createElement('div');
      item.className = 'file-item';
      const sizeKb = (f.size / 1024).toFixed(1);
      item.innerHTML = `
        <span class="file-name" title="${f.name}">📄 ${f.name} <small style="color:#64748b">(${sizeKb} KB)</small></span>
        <button class="file-remove" onclick="removerArchivo(${idx})">×</button>
      `;
      contenedor.appendChild(item);
    });

    const habilitar = listaArchivos.length > 0;
    document.getElementById('btnDescargar').disabled = !habilitar;
    document.getElementById('btnImprimir').disabled = !habilitar;
  }

  function removerArchivo(idx) {
    listaArchivos.splice(idx, 1);
    actualizarListaUI();
    if (listaArchivos.length > 0) {
      actualizarPrevisualizacion();
    } else {
      limpiarTodo();
    }
  }

  function limpiarTodo() {
    listaArchivos = [];
    actualizarListaUI();
    document.getElementById('fileInput').value = '';
    document.getElementById('statsRow').style.display = 'none';
    document.getElementById('previewImage').style.display = 'none';
    document.getElementById('previewPlaceholder').style.display = 'block';
  }

  async function actualizarPrevisualizacion() {
    if (listaArchivos.length === 0) return;

    const formData = new FormData();
    listaArchivos.forEach(f => formData.append('files', f));
    formData.append('tamano', document.getElementById('tamanoPapel').value);
    formData.append('linea_corte', document.getElementById('lineaCorte').checked);
    formData.append('margen', document.getElementById('margenRecorte').value);

    try {
      const resp = await fetch('/api/preview', { method: 'POST', body: formData });
      if (!resp.ok) return;
      const data = await resp.json();

      document.getElementById('statComprobantes').innerText = data.total_comprobantes;
      document.getElementById('statHojas').innerText = data.total_hojas;
      const ahorro = data.total_comprobantes > 0 
        ? Math.round((1 - (data.total_hojas / data.total_comprobantes)) * 100) 
        : 50;
      document.getElementById('statAhorro').innerText = (ahorro > 0 ? ahorro : 0) + '%';
      document.getElementById('statsRow').style.display = 'grid';

      if (data.preview_base64) {
        const img = document.getElementById('previewImage');
        img.src = 'data:image/png;base64,' + data.preview_base64;
        img.style.display = 'block';
        document.getElementById('previewPlaceholder').style.display = 'none';
      }
    } catch (err) {
      console.error("Error al obtener preview:", err);
    }
  }

  async function procesarYDescargar(abrirImpresion) {
    if (listaArchivos.length === 0) return;

    const btn = document.getElementById('btnDescargar');
    const spinner = document.getElementById('spinnerDescargar');
    const txt = document.getElementById('btnTextDescargar');
    btn.disabled = true;
    spinner.style.display = 'inline-block';
    txt.innerText = 'Procesando comprobantes...';

    const formData = new FormData();
    listaArchivos.forEach(f => formData.append('files', f));
    formData.append('tamano', document.getElementById('tamanoPapel').value);
    formData.append('linea_corte', document.getElementById('lineaCorte').checked);
    formData.append('margen', document.getElementById('margenRecorte').value);

    try {
      const resp = await fetch('/api/procesar', { method: 'POST', body: formData });
      if (!resp.ok) {
        const err = await resp.text();
        alert('Error: ' + err);
        return;
      }
      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);

      if (abrirImpresion) {
        // Abre en nueva pestaña para ver e imprimir con Ctrl+P
        window.open(url, '_blank');
      } else {
        // Descarga directa
        const a = document.createElement('a');
        a.href = url;
        a.download = 'comprobantes_2xhoja.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
    } catch (err) {
      alert('Error de conexión con el servidor: ' + err);
    } finally {
      btn.disabled = false;
      spinner.style.display = 'none';
      txt.innerText = '💾 Descargar PDF Combinado';
    }
  }
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def inicio():
    ips = obtener_ips_locales()
    ip_principal = ips[0] if ips else "localhost"
    html = HTML_TEMPLATE.replace("{{LOCAL_IP}}", ip_principal)
    return HTMLResponse(content=html)


@app.get("/api/info")
async def info():
    return {
        "status": "online",
        "servicio": "Unificador de Comprobantes 2x1",
        "ips": obtener_ips_locales(),
        "puerto": 8000
    }


@app.post("/api/preview")
async def api_preview(
    files: List[UploadFile] = File(...),
    tamano: str = Form("A4"),
    linea_corte: bool = Form(True),
    margen: float = Form(6.0)
):
    """Genera conteo de páginas y preview PNG de la primera hoja combinada."""
    if not files:
        raise HTTPException(status_code=400, detail="Debe adjuntar al menos un archivo PDF.")

    fuentes = []
    for f in files:
        contenido = await f.read()
        fuentes.append(contenido)

    pdf_bytes, total_comp, total_hojas = procesar_comprobantes(
        fuentes=fuentes,
        tamano_papel=tamano,
        linea_corte=linea_corte,
        margen_extra=margen
    )

    if total_comp == 0:
        return JSONResponse({"total_comprobantes": 0, "total_hojas": 0, "preview_base64": ""})

    png_bytes = obtener_preview_png(pdf_bytes, dpi=130)
    preview_b64 = base64.b64encode(png_bytes).decode("ascii") if png_bytes else ""

    return {
        "total_comprobantes": total_comp,
        "total_hojas": total_hojas,
        "preview_base64": preview_b64
    }


@app.post("/api/procesar")
async def api_procesar(
    files: List[UploadFile] = File(...),
    tamano: str = Form("A4"),
    linea_corte: bool = Form(True),
    margen: float = Form(6.0)
):
    """Procesa los PDFs y descarga el PDF final combinado."""
    if not files:
        raise HTTPException(status_code=400, detail="Debe adjuntar al menos un archivo PDF.")

    fuentes = []
    for f in files:
        contenido = await f.read()
        fuentes.append(contenido)

    pdf_bytes, total_comp, total_hojas = procesar_comprobantes(
        fuentes=fuentes,
        tamano_papel=tamano,
        linea_corte=linea_corte,
        margen_extra=margen
    )

    if total_comp == 0:
        raise HTTPException(status_code=400, detail="No se encontraron páginas válidas en los PDFs.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=comprobantes_2xhoja.pdf"
        }
    )


@app.get("/healthz")
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "unificador-comprobantes-2x1"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    ips = obtener_ips_locales()
    print("=" * 60)
    print("  🚀 SERVICIO WEB DE UNIÓN DE COMPROBANTES INICIADO")
    print("=" * 60)
    print(f"  Puerto configurado: {port}")
    print(f"  Acceso local: http://localhost:{port}")
    for ip in ips:
        print(f"  Acceso red: http://{ip}:{port}")
    print("=" * 60)
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
