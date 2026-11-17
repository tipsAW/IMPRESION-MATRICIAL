# -*- coding: utf-8 -*-
"""
Une comprobantes de egreso (PDF con contenido en media hoja A4/Carta)
de dos en dos, para imprimir 2 por hoja.
Compatible con archivos individuales o un solo PDF de múltiples páginas (ej. 50+ páginas).
"""

import os
import platform
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox

from procesador import procesar_comprobantes, TAMANOS


# ----------------------------------------------------------------------
# Impresión
# ----------------------------------------------------------------------
def enviar_a_impresora(ruta_pdf):
    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(ruta_pdf, "print")
        elif sistema == "Darwin":
            subprocess.run(["lp", ruta_pdf], check=True)
        else:
            subprocess.run(["lp", ruta_pdf], check=True)
        return True, ""
    except Exception as e:
        return False, str(e)


# ----------------------------------------------------------------------
# Interfaz Gráfica de Escritorio
# ----------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Unir comprobantes – 2 por hoja A4 / Carta")
        root.geometry("720x520")

        self.archivos = []
        self.tamano_papel = tk.StringVar(value="A4")
        self.linea_corte = tk.BooleanVar(value=True)

        barra = tk.Frame(root)
        barra.pack(fill="x", padx=10, pady=8)
        tk.Button(barra, text="➕ Agregar PDFs…", command=self.agregar, font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Button(barra, text="✖ Quitar seleccionado", command=self.quitar).pack(side="left", padx=6)
        tk.Button(barra, text="🗑 Limpiar lista", command=self.limpiar).pack(side="left")

        # Configuración de tamaño
        opc_frame = tk.Frame(barra)
        opc_frame.pack(side="right")
        tk.Label(opc_frame, text="Papel:").pack(side="left", padx=(10, 4))
        tk.OptionMenu(opc_frame, self.tamano_papel, "A4", "Carta").pack(side="left")
        tk.Checkbutton(opc_frame, text="Línea corte", variable=self.linea_corte).pack(side="left", padx=6)

        self.lista = tk.Listbox(root, selectmode="extended", font=("Consolas", 9))
        self.lista.pack(fill="both", expand=True, padx=10)

        pie = tk.Frame(root)
        pie.pack(fill="x", padx=10, pady=8)
        tk.Button(pie, text="💾 Guardar PDF combinado…",
                  command=self.generar, height=2, bg="#2563eb", fg="white",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Button(pie, text="🖨 Imprimir directo",
                  command=self.imprimir, height=2, font=("Segoe UI", 10)).pack(side="left", padx=8)

        self.estado = tk.Label(root, text="0 archivos cargados", anchor="w", font=("Segoe UI", 9, "bold"))
        self.estado.pack(fill="x", padx=10, pady=(0, 4))

        tk.Label(root,
                 text="Nota: Soporta 1 solo PDF con 50+ páginas o múltiples archivos individuales.",
                 fg="#475569").pack(fill="x", padx=10, pady=(0, 8))

    # ------------------------------------------------------------------
    def refrescar(self):
        self.lista.delete(0, tk.END)
        for a in self.archivos:
            self.lista.insert(tk.END, os.path.basename(a))
        self.estado.config(text=f"{len(self.archivos)} archivo(s) en lista.")

    def agregar(self):
        rutas = filedialog.askopenfilenames(
            title="Seleccionar comprobantes PDF",
            filetypes=[("PDF", "*.pdf")])
        for r in rutas:
            if r not in self.archivos:
                self.archivos.append(r)
        self.refrescar()

    def quitar(self):
        sel = list(self.lista.curselection())
        for i in reversed(sel):
            del self.archivos[i]
        self.refrescar()

    def limpiar(self):
        self.archivos.clear()
        self.refrescar()

    # ------------------------------------------------------------------
    def generar(self):
        if not self.archivos:
            messagebox.showwarning("Sin archivos", "Agrega al menos un PDF.")
            return None
        destino = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="comprobantes_2xhoja.pdf")
        if not destino:
            return None
        try:
            pdf_bytes, total_comp, total_hojas = procesar_comprobantes(
                fuentes=self.archivos,
                tamano_papel=self.tamano_papel.get(),
                linea_corte=self.linea_corte.get()
            )
            with open(destino, "wb") as f:
                f.write(pdf_bytes)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar:\n{e}")
            return None
        messagebox.showinfo(
            "Listo",
            f"Proceso completado exitosamente:\n\n"
            f"• Comprobantes leídos: {total_comp}\n"
            f"• Hojas generadas: {total_hojas}\n\n"
            f"Guardado en: {destino}")
        return destino

    def imprimir(self):
        if not self.archivos:
            messagebox.showwarning("Sin archivos", "Agrega al menos un PDF.")
            return
        tmp = os.path.join(tempfile.gettempdir(), "comprobantes_2xhoja.pdf")
        try:
            pdf_bytes, total_comp, total_hojas = procesar_comprobantes(
                fuentes=self.archivos,
                tamano_papel=self.tamano_papel.get(),
                linea_corte=self.linea_corte.get()
            )
            with open(tmp, "wb") as f:
                f.write(pdf_bytes)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo preparar el PDF:\n{e}")
            return

        ok, err = enviar_a_impresora(tmp)
        if ok:
            messagebox.showinfo(
                "Enviado a impresora",
                f"Se procesaron {total_comp} comprobantes en {total_hojas} hojas.\n\n"
                f"Se envió a la impresora predeterminada.\n"
                f"Si no imprime automáticamente, puedes abrir el archivo temporal:\n{tmp}")
        else:
            messagebox.showerror("Error al imprimir", err)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
