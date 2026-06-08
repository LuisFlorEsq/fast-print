import os
import sys
import tkinter as tk
from PIL import Image

from tkinter import ttk, filedialog, messagebox
from threading import Thread


from src.core.image import resize_image_to_cm, save_image_for_printing
from src.core.grid import create_grid_canvas
from src.core.document import extract_text_from_docx, convert_text_to_printable_images
from src.core.printer import send_to_system_printer, get_available_printers


from src.config import (IMAGE_EXTENSIONS, DOC_EXTENSIONS, TARGET_DPI)

AVAILABLE_EXTENSIONS = [
    (
        "Todos los archivos soportados", 
        " ".join(f"*{ext}" for ext in (IMAGE_EXTENSIONS + DOC_EXTENSIONS))
    ),
    (
        "Imágenes", 
        " ".join(f"*{ext}" for ext in IMAGE_EXTENSIONS)
    ),
    (
        "Documentos", 
        " ".join(f"*{ext}" for ext in DOC_EXTENSIONS)
    )
]


class FastPrintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fast Print Tool")
        self.root.geometry("520x450")
        self.root.resizable(False, False)

        # Configure TTK style context
        self.style = ttk.Style()
        self.style.theme_use("vista")

        # Application State
        self.selected_path = tk.StringVar()
        self.target_printer = tk.StringVar()
        self.page_type = tk.StringVar(value="letter")
        self.is_grid_enabled = tk.BooleanVar(value=False)
        self.is_print_enabled = tk.BooleanVar(value=True)

        self._build_ui()
        self._load_printers()

    def _build_ui(self):
        """
        Constructs clean, scannable visual layout with proper padding.
        """
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---------------------------------------------------------------------
        # SECTION 1: File Selection Context
        # ---------------------------------------------------------------------
        file_lf = ttk.LabelFrame(
            main_frame, text="Archivo o Carpeta Origen", padding="10")
        file_lf.pack(fill=tk.X, pady=(0, 15))

        file_entry = ttk.Entry(
            file_lf, textvariable=self.selected_path, width=40, state="readonly")
        file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        browse_btn = ttk.Button(file_lf, text="Buscar...",
                                command=self._handle_browse)
        browse_btn.pack(side=tk.RIGHT)

        # ---------------------------------------------------------------------
        # SECTION 2: Layout processing configuration
        # ---------------------------------------------------------------------
        config_lf = ttk.LabelFrame(
            main_frame, text="Configuración de Página", padding="10")
        config_lf.pack(fill=tk.X, pady=(0, 15))

        # Row 1: Dimensions Input
        dim_frame = ttk.Frame(config_lf)
        dim_frame.pack(fill=tk.X, pady=5)

        ttk.Label(dim_frame, text="Ancho (cm):").pack(side=tk.LEFT, padx=2)
        self.width_ent = ttk.Entry(dim_frame, width=8)
        self.width_ent.pack(side=tk.LEFT, padx=10)

        ttk.Label(dim_frame, text="Alto (cm):").pack(side=tk.LEFT, padx=2)
        self.height_ent = ttk.Entry(dim_frame, width=8)
        self.height_ent.pack(side=tk.LEFT, padx=10)

        # Row 2: Grid activation controls
        grid_frame = ttk.Frame(config_lf)
        grid_frame.pack(fill=tk.X, pady=5)

        grid_chk = ttk.Checkbutton(
            grid_frame,
            text="Activar Cuadrícula N-up (Multi-copias)",
            variable=self.is_grid_enabled,
            command=self._toggle_grid_options
        )
        grid_chk.pack(side=tk.LEFT)

        self.grid_combo = ttk.Combobox(
            grid_frame, values=["2", "4", "6", "8"], width=5, state="disabled")
        self.grid_combo.set("4")
        self.grid_combo.pack(side=tk.LEFT, padx=10)

        # Row 3: Page Constraint Context
        page_frame = ttk.Frame(config_lf)
        page_frame.pack(fill=tk.X, pady=5)

        ttk.Label(page_frame, text="Tamaño de papel:").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(page_frame, text="Carta (Letter)",
                        variable=self.page_type, value="letter").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(page_frame, text="A4", variable=self.page_type,
                        value="a4").pack(side=tk.LEFT, padx=10)

        # ---------------------------------------------------------------------
        # SECTION 3: Hardware Print Routing
        # ---------------------------------------------------------------------
        hardware_lf = ttk.LabelFrame(
            main_frame, text="Enrutamiento de Hardware", padding=10)
        hardware_lf.pack(fill=tk.X, pady=(0, 20))

        print_chk = ttk.Checkbutton(
            hardware_lf, text="Enviar directo a la impresora", variable=self.is_print_enabled)
        print_chk.pack(side=tk.LEFT, padx=5)

        self.printer_combo = ttk.Combobox(
            hardware_lf, textvariable=self.target_printer, state="readonly", width=30)
        self.printer_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # ---------------------------------------------------------------------
        # SECTION 4: Execution context and Progress Status Bar
        # ---------------------------------------------------------------------

        self.action_btn = ttk.Button(
            main_frame, text="Iniciar Procesamiento Rapido", command=self._execute_thread)
        self.action_btn.pack(fill=tk.X, ipady=5)

        self.status_lbl = ttk.Label(main_frame, text="Estado: Listo", font=(
            "Segoe UI", 9, "italic"), foreground="gray")
        self.status_lbl.pack(anchor=tk.W, pady=(5, 0))

    def _handle_browse(self):
        """
        Asks user for file layout type
        """
        file_path = filedialog.askopenfilename(filetypes=AVAILABLE_EXTENSIONS)
        if file_path:
            self.selected_path.set(file_path)
            if file_path.lower().endswith(('pdf', '.docx')):
                self.width_ent.delete(0, tk.END)
                self.height_ent.delete(0, tk.END)
                self.width_ent.config(state="disabled")
                self.height_ent.config(state="disabled")
            else:
                self.width_ent.config(state="normal")
                self.height_ent.config(state="normal")

    def _toggle_grid_options(self):
        """
        UX Toggler for Combobox constraints
        """
        if self.is_grid_enabled.get():
            self.grid_combo.config(state="readonly")
        else:
            self.grid_combo.config(state="disabled")

    def _load_printers(self):
        """
        Asynchronously loads target devices to prevent window freezing
        """
        try:
            printers = get_available_printers()
            self.printer_combo['values'] = printers
            if printers:
                self.printer_combo.set(printers[0])  # Initial value
        except Exception:
            self.printer_combo['values'] = ["Default Printer"]
            self.printer_combo.set("Default Printer")

    def _execute_thread(self):
        """
        Spawns a separate execution thread to maintain UI responsiveness
        """
        if not self.selected_path.get():
            messagebox.showwarning(
                "Falta informacion", "Por Favor, selecciona un archivo válido antes de continuar")
            return

        self.action_btn.config(state="disabled")
        self.status_lbl.config(
            text="Estado: Procesando archivo en segundo plano... Por favor espera", foreground="blue")

        worker = Thread(target=self._process_core_logic)
        worker.daemon = True
        worker.start()

    def _process_core_logic(self):
        """
        Translates graphical state into precise decoupled core execution routines.
        """
        try:
            path = self.selected_path.get()
            dpi = TARGET_DPI
            print_now = self.is_print_enabled.get()
            printer = self.target_printer.get()
            grid_enabled = self.is_grid_enabled.get()
            grid_size = int(self.grid_combo.get()) if grid_enabled else None
            page = self.page_type.get()

            # Execution Papeline
            final_output = None

            # --- Document Flow (pdf, docx) ---
            if path.lower().endswith('.pdf'):
                if not grid_enabled and print_now:
                    send_to_system_printer(
                        file_path=path, printer_name=printer, watch_status=True)
                else:
                    raise ValueError(
                        "Para procesar un PDF en cuadricula usa el comando CLI o conviertelo previamente")

            elif path.lower().endswith('.docx'):
                text = extract_text_from_docx(file_path=path)
                pages = convert_text_to_printable_images(text, dpi=dpi)
                final_output = f"{os.path.splitext(path)[0]}_temp_print.png"

                if grid_enabled:
                    canvas = create_grid_canvas(
                        images=pages, grid_size=grid_size, page_type=page, dpi=dpi)
                    save_image_for_printing(
                        img=canvas, output_path=final_output, dpi=dpi)
                    if print_now:
                        send_to_system_printer(
                            file_path=final_output, printer_name=printer, watch_status=True)

                else:
                    for idx, pg in enumerate(pages, 1):
                        final_output = f"{os.path.splitext(path)[0]}_page_{idx}.png"
                        save_image_for_printing(img=pg, output_path=final_output, dpi=dpi)
                        if print_now:
                            send_to_system_printer(file_path=final_output, printer_name=printer, watch_status=True)
            
            # --- Image Processing flow ---
            else:
                w_cm = float(self.width_ent.get()) if self.width_ent.get() else None
                h_cm = float(self.height_ent.get()) if self.height_ent.get() else None
                final_output = f"{os.path.splitext(path)[0]}_processed_gui.png"
                
                if grid_enabled:
                    with Image.open(path) as img:
                        canvas = create_grid_canvas([img] * grid_size, grid_size=grid_size, page_type=page, dpi=dpi)
                        save_image_for_printing(img=canvas, output_path=final_output, dpi=dpi)
                else:
                    img = resize_image_to_cm(path, width_cm=w_cm, height_cm=h_cm, dpi=dpi)
                    save_image_for_printing(img=img, output_path=final_output, dpi=dpi)
                
                if print_now and final_output and os.path.exists(final_output):
                    send_to_system_printer(file_path=final_output, printer_name=printer, watch_status=True)
                    
            self.root.after(0, self._handle_success)
            
        except Exception as e:
            self.root.after(0, lambda: self._hadle_error(str(e)))
            
    
    def _handle_success(self):
        self.action_btn.config(state="normal")
        self.status_lbl.config(text="Estado: ¡Operación completada con éxito en el hardware!", foreground="green")
        messagebox.showinfo("Éxito", "El documento ha sido procesado e impreso de forma segura.")

    def _handle_error(self, err_msg: str):
        self.action_btn.config(state="normal")
        self.status_lbl.config(text="Estado: Error en la cola de impresión.", foreground="red")
        messagebox.showerror("Error de Procesamiento", f"Ocurrió un fallo: {err_msg}")
                
                        


if __name__ == "__main__":
    root = tk.Tk()
    app = FastPrintApp(root)
    root.mainloop()