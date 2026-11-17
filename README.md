# 📄 Unificador de Comprobantes 2x1 (A4 y Carta / Matricial)

Une comprobantes de egreso (cuyo contenido ocupa la mitad de una hoja) de 2 en 2 por hoja para ahorrar el 50% de papel.

Soporta:
1. **Un solo archivo PDF con múltiples páginas** (ej. 50 o 55 páginas en un solo PDF).
2. **Múltiples archivos PDF independientes** (ej. 50 archivos de 1 página cada uno).
3. **Mezcla de archivos**: El sistema extrae todas las páginas en orden y las combina de 2 en 2.

---

## 🌐 1. Modo Servicio Web (Para compartir en la Red Local)

Permite que cualquier persona en la oficina o red local use la herramienta desde su navegador sin tener que instalar Python.

### Iniciar el servidor:
- Haz doble clic en **`iniciar_web.bat`** (o corre `python app.py`).
- El servidor mostrará las direcciones de acceso:
  - **En tu equipo**: `http://localhost:8000`
  - **En la red local (compartir con compañeros)**: `http://192.168.102.25:8000` (o la IP que indique la consola).

### Características Web:
- **Arrastrar y soltar** (Drag & Drop) de PDFs.
- **Vista previa visual en vivo** de la primera hoja combinada.
- Contador automático: *55 comprobantes → 28 hojas finales (Ahorro: 49%)*.
- Selector de tamaño: **A4** (210×297 mm) o **Carta / Letter** (8.5×11 in).
- Opción de **Línea punteada divisoria central** (ideal para doblar o guillotinar).
- Botón **Descargar PDF** y **Abrir para Imprimir directo** (`Ctrl + P`).

---

## 🖥️ 2. Modo Escritorio (Ventana de Windows)

Si prefieres usar la aplicación clásica de escritorio en tu PC:
- Haz doble clic en **`iniciar.bat`** (o corre `python unir_comprobantes.py`).

---

## 📦 Requisitos e Instalación

Todas las dependencias están en `requirements.txt`:
```bash
pip install -r requirements.txt
```
*(Requiere: `pymupdf`, `fastapi`, `uvicorn`, `python-multipart`)*

---

## 🖨️ Recomendaciones para Impresora Matricial / Papel Continuo

1. **Tamaño del Papel**:
   - Si usas papel continuo de media página o tamaño carta continuo, selecciona **Carta / Letter**. Si usas formato continuo A4, selecciona **A4**.
2. **Línea Divisoria**:
   - Mantén activada la opción de línea punteada divisoria si necesitas una referencia visual exacta para el corte o perforación.
3. **Escalado al imprimir**:
   - En el cuadro de diálogo de impresión de Windows (`Ctrl + P`), asegúrate de que la escala esté en **100% / Tamaño real** (desactiva "ajustar a la página" para evitar desplazamientos).
