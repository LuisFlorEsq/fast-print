import os
import tkinter as tk
from contextlib import ExitStack
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from PIL import Image, ImageTk

from src.core import exceptions
from src.core.printer import PrintManager
from src.processing.docs.doc_strategy import print_document_smart
from src.processing.images.grid import create_grid_canvas
from src.processing.images.image import resize_image_to_cm, save_image_for_printing
from src.utils import validators
from src.utils.config import DOC_EXTENSIONS, IMAGE_EXTENSIONS, TARGET_DPI
from src.utils.logger import logger

AVAILABLE_EXTENSIONS = [
    (
        "Todos los archivos soportados",
        " ".join(f"*{ext}" for ext in (IMAGE_EXTENSIONS + DOC_EXTENSIONS)),
    ),
    ("Imágenes", " ".join(f"*{ext}" for ext in IMAGE_EXTENSIONS)),
    ("Documentos", " ".join(f"*{ext}" for ext in DOC_EXTENSIONS)),
]


class FastPrintApp:
    """
    Core GUI Class that manages the fast print
    tool workflow and user interactions.
    """

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
        self.is_directory = tk.BooleanVar(value=False)
        self.target_printer = tk.StringVar()
        self.page_type = tk.StringVar(value="letter")
        self.is_grid_enabled = tk.BooleanVar(value=False)
        self.is_print_enabled = tk.BooleanVar(value=True)

        # References for visual preview tracking
        self.modal_preview_img_ref = None

        self._build_ui()
        self._load_printers()

    def _build_ui(self):
        """
        Constructs clean, scannable visual layout with proper padding.
        """
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---------------------------------------------------------------------
        # SECTION 1: Source Selection Context (File or Folder)
        # ---------------------------------------------------------------------
        file_lf = ttk.LabelFrame(main_frame, text="Archivo o Carpeta Origen", padding="10")
        file_lf.pack(fill=tk.X, pady=(0, 15))

        file_entry = ttk.Entry(
            file_lf, textvariable=self.selected_path, width=40, state="readonly"
        )
        file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        browse_file_btn = ttk.Button(file_lf, text="Archivo...", command=self._handle_browse_file)
        browse_file_btn.pack(side=tk.LEFT, padx=2)

        browse_dir_btn = ttk.Button(
            file_lf, text="Carpeta...", command=self._handle_browse_directory
        )
        browse_dir_btn.pack(side=tk.LEFT, padx=2)

        # ---------------------------------------------------------------------
        # SECTION 2: Layout processing configuration
        # ---------------------------------------------------------------------
        config_lf = ttk.LabelFrame(main_frame, text="Configuración de Página", padding="10")
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

        self.grid_chk = ttk.Checkbutton(
            grid_frame,
            text="Activar Cuadrícula N-up (Multi-copias)",
            variable=self.is_grid_enabled,
            command=self._toggle_grid_options,
        )
        self.grid_chk.pack(side=tk.LEFT)

        self.grid_combo = ttk.Combobox(
            grid_frame, values=["2", "4", "6", "8"], width=5, state="disabled"
        )
        self.grid_combo.set("4")
        self.grid_combo.pack(side=tk.LEFT, padx=10)

        # Row 3: Page Constraint Context
        page_frame = ttk.Frame(config_lf)
        page_frame.pack(fill=tk.X, pady=5)

        ttk.Label(page_frame, text="Tamaño de papel:").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(
            page_frame, text="Carta (Letter)", variable=self.page_type, value="letter"
        ).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(page_frame, text="A4", variable=self.page_type, value="a4").pack(
            side=tk.LEFT, padx=10
        )

        # ---------------------------------------------------------------------
        # SECTION 3: Hardware Print Routing
        # ---------------------------------------------------------------------
        hardware_lf = ttk.LabelFrame(main_frame, text="Enrutamiento de Hardware", padding=10)
        hardware_lf.pack(fill=tk.X, pady=(0, 20))

        print_chk = ttk.Checkbutton(
            hardware_lf,
            text="Enviar directo a la impresora",
            variable=self.is_print_enabled,
        )
        print_chk.pack(side=tk.LEFT, padx=5)

        self.printer_combo = ttk.Combobox(
            hardware_lf, textvariable=self.target_printer, state="readonly", width=30
        )
        self.printer_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # ---------------------------------------------------------------------
        # SECTION 4: Execution context and Progress Status Bar
        # ---------------------------------------------------------------------

        self.action_btn = ttk.Button(
            main_frame, text="Generar vista previa", command=self._execute_thread
        )
        self.action_btn.pack(fill=tk.X, ipady=5)

        self.status_lbl = ttk.Label(
            main_frame,
            text="Estado: Listo",
            font=("Segoe UI", 9, "italic"),
            foreground="gray",
        )
        self.status_lbl.pack(anchor=tk.W, pady=(5, 0))

    def _handle_browse_file(self):
        """
        Handles individual file browsing selection
        """
        file_path = filedialog.askopenfilename(filetypes=AVAILABLE_EXTENSIONS)
        if file_path:
            self.selected_path.set(file_path)
            self.is_directory.set(False)
            self._adapt_ux_fields(
                is_folder=False, is_doc=file_path.lower().endswith((".pdf", ".docx"))
            )

    def _handle_browse_directory(self):
        """
        Handles complete folder scanning selection
        """
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.selected_path.set(dir_path)
            self.is_directory.set(True)
            self._adapt_ux_fields(is_folder=True, is_doc=False)

    def _adapt_ux_fields(self, is_folder: bool, is_doc: bool):
        """
        Best practices for clean interface workflow constraints

        Args:
            is_folder (bool): Flag to detect Folder/Directory flow
            is_doc (bool): Flag to detect document flow
        """

        if is_folder:
            # Building automatic grids
            self.width_ent.delete(0, tk.END)
            self.height_ent.delete(0, tk.END)

            self.width_ent.config(state="disabled")
            self.height_ent.config(state="disabled")

            self.is_grid_enabled.set(True)
            self.grid_combo.config(state="readonly")

        elif is_doc:
            # Word or PDF documents have predefined text metrics
            self.width_ent.delete(0, tk.END)
            self.height_ent.delete(0, tk.END)

            self.width_ent.config(state="disabled")
            self.height_ent.config(state="disabled")

            self.is_grid_enabled.set(False)
            self.grid_combo.config(state="disabled")

        else:
            # Standard simple image
            self.width_ent.config(state="normal")
            self.height_ent.config(state="normal")

            self.is_grid_enabled.set(False)
            self.grid_combo.config(state="disabled")

    def _toggle_grid_options(self):
        """
        UX Toggler for Combobox constraints
        """
        if self.is_grid_enabled.get():
            self.grid_combo.config(state="readonly")
        else:
            if self.is_directory.get():
                self.is_grid_enabled.set(True)
                messagebox.showwarning(
                    "Restriccion",
                    "El procesamiento de carpetas requiere activar la cuadricula",
                )
            else:
                self.grid_combo.config(state="disabled")

    def _load_printers(self):
        """
        Asynchronously loads target devices to prevent window freezing.
        Utilizes the Singleton manager to fetch hardware devices safely.
        """
        try:
            # Instantiate the Singleton manager
            printer_manager = PrintManager()
            printers = printer_manager.get_available_printers()
            self.printer_combo["values"] = printers

            if printers:
                self.printer_combo.set(printers[0])  # Initial value
        except exceptions.PrinterNotFoundError as e:
            messagebox.showerror("Printer Error", str(e))
            self.printer_combo["values"] = ["Default Printer"]
            self.printer_combo.set("Default Printer")

    def _execute_thread(self):
        """
        Spawns a separate execution thread to maintain UI responsiveness
        """
        if not self.selected_path.get():
            messagebox.showwarning(
                "Falta informacion",
                "Por Favor, selecciona un archivo válido antes de continuar",
            )
            return

        # Inputh fields validation
        try:
            selected_path = self.selected_path.get()
            validators.validate_path(selected_path)

            page = self.page_type.get()
            validators.validate_page_type(page)

            printer = self.target_printer.get()
            available_printers = list(self.printer_combo["values"])
            validators.validate_printer(printer, available_printers)

            width = float(self.width_ent.get()) if self.width_ent.get() else None
            height = float(self.height_ent.get()) if self.height_ent.get() else None

            if not self.is_directory.get():
                extension = selected_path.lower()

                if extension.endswith((".png", ".jpg", ".jpeg")):
                    validators.validate_image_file(selected_path)

                    if not self.is_grid_enabled.get():
                        validators.validate_dimensions(width, height)
                        validators.validate_image_fits(width, height, page)

                elif extension.endswith(".pdf"):
                    validators.validate_pdf_file(selected_path)

                elif extension.endswith(".docx"):
                    validators.validate_docx_file(selected_path)

        except exceptions.ValidationError as e:
            messagebox.showerror(
                "Validation error", str(e)
            )
            return

        except exceptions.ValidationError as e:
            logger.warning(f"Validation failed: {e}")
            messagebox.showerror("Validation Error", str(e))
            return

        self.action_btn.config(state="disabled")
        self.status_lbl.config(
            text="Estado: Procesando archivo en segundo plano... Por favor espera",
            foreground="blue",
        )

        # Extract all Tkinter variables safely in the main thread
        ui_state = {
            "path": selected_path,
            "printer": printer,
            "page": page,
            "w_cm": width,
            "h_cm": height,
            "grid_enabled": self.is_grid_enabled.get(),
            "grid_size": int(self.grid_combo.get()) if self.is_grid_enabled.get() else None,
            "is_dir": self.is_directory.get(),
            "print_now": self.is_print_enabled.get(),
        }

        worker = Thread(target=self._process_core_logic, kwargs=ui_state)
        worker.daemon = True
        worker.start()

    def _process_core_logic(
        self,
        path: str,
        is_dir: bool,
        print_now: bool,
        printer: Optional[str],
        grid_enabled: bool,
        grid_size: int,
        page: str,
        w_cm: float,
        h_cm: float,
    ):
        """
        Translates graphical state into precise decoupled core execution routines.
        """
        try:
            dpi = TARGET_DPI
            final_output = None

            # ---------------------------------------------------------------------
            # PIPELINE FLOW 1: Folder Batch processing
            # ---------------------------------------------------------------------
            if is_dir:
                file_list = [
                    os.path.join(path, f)
                    for f in os.listdir(path)
                    if f.lower().endswith(tuple(IMAGE_EXTENSIONS))
                ]

                if not file_list:
                    raise ValueError(
                        "No se encontraron imágenes compatibles (.jpg, .png) en la carpeta"
                    )

                output_dir = os.path.join(path, "FastPrint_Output")
                os.makedirs(name=output_dir, exist_ok=True)

                page_number = 1
                for i in range(0, len(file_list), grid_size):
                    chunk_paths = file_list[i : i + grid_size]

                    with ExitStack() as stack:
                        chunk_images = [stack.enter_context(Image.open(p)) for p in chunk_paths]

                        with create_grid_canvas(
                            images=chunk_images,
                            grid_size=grid_size,
                            page_type=page,
                            dpi=dpi,
                        ) as grid_canvas:
                            final_output = os.path.join(
                                output_dir, f"gui_grid_page_{page_number}_{page}.png"
                            )

                            save_image_for_printing(
                                img=grid_canvas, output_path=final_output, dpi=dpi
                            )

                    page_number += 1
            # ---------------------------------------------------------------------
            # PIPELINE FLOW 2: Individual Document or Image processing
            # ---------------------------------------------------------------------
            else:
                # --- Document Flow (pdf, docx) ---
                if path.lower().endswith((".pdf", ".docx")):
                    final_output = path

                # --- Standard Image processing ---
                else:
                    final_output = f"{os.path.splitext(path)[0]}_processed_gui.png"

                    if grid_enabled:
                        with Image.open(path) as source_img:
                            with create_grid_canvas(
                                [source_img] * grid_size,
                                grid_size=grid_size,
                                page_type=page,
                                dpi=dpi,
                            ) as canvas:
                                save_image_for_printing(
                                    img=canvas, output_path=final_output, dpi=dpi
                                )

                    else:
                        with resize_image_to_cm(
                            path, width_cm=w_cm, height_cm=h_cm, page_type=page, dpi=dpi
                        ) as processed_img:
                            save_image_for_printing(
                                img=processed_img, output_path=final_output, dpi=dpi
                            )

            self.root.after(
                0,
                lambda: self._open_preview_modal(
                    output_path=final_output, printer=printer, page=page
                ),
            )

        except exceptions.FastPrintError as e:
            logger.exception("Error captured in the background print processing thread.")
            error_clean_msg = exceptions.translate_exception(e)

            self.root.after(0, lambda: self._handle_error(err_msg=error_clean_msg))

    def _open_preview_modal(self, output_path: str, printer: str, page: str):
        """
        Creates a modern separate popup window for verifying layout components before printing

        Args:
            output_path (str): Path of the target Images/Documents
            printer (str): Target device
            page (str): Page type (Letter, A4)
        """

        self.action_btn.config(state="normal")
        self.status_lbl.config(text="Estado: Vista previa lista", foreground="green")

        # Window configuration
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Vista previa de impresión")
        preview_win.geometry("450x530")
        preview_win.resizable(False, False)

        preview_win.grab_set()  # Blocks interaction with the background window

        container = ttk.Frame(preview_win, padding=15)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="Confirma el diseño final antes de imprimir:",
            font=("Segoe UI", 10, "bold"),
        ).pack(pady=(0, 10))

        # Core graphic vieweing frame
        viewer_lf = ttk.Label(container, text="Renderizado de pagina", padding=5)
        viewer_lf.pack(fill=tk.BOTH, expand=True)

        display_lbl = ttk.Label(viewer_lf, anchor="center", justify="center")
        display_lbl.pack(fill=tk.BOTH, expand=True)

        file_extension = os.path.splitext(output_path)[1].lower()

        if file_extension in [".pdf", ".docx"]:
            display_lbl.config(
                text="Vista previa no disponible\n"
                f"Para archivos nativos {file_extension.upper()}.\n\n"
                "El archivo está listo para ser enviado\nal hardware de forma segura."
            )
            self.modal_preview_img_ref = None

        else:
            try:
                with Image.open(output_path) as img:
                    preview_copy = img.copy()
                    preview_copy.thumbnail((360, 360), Image.Resampling.BILINEAR)
                    self.modal_preview_img_ref = ImageTk.PhotoImage(preview_copy)
                    display_lbl.config(image=self.modal_preview_img_ref)

            except exceptions.FastPrintError as e:
                display_lbl.config(text=f"Error al cargar la visualizacion detallada:\n{str(e)}")

        # Action buttons Layout
        actions_frame = ttk.Frame(container)
        actions_frame.pack(fill=tk.X, pady=(15, 0))

        cancel_btn = ttk.Button(actions_frame, text="Cancelar", command=preview_win.destroy)
        cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        print_btn = ttk.Button(
            actions_frame,
            text="Imprimir ahora",
            command=lambda: self._send_to_hardware(
                output_path=output_path, printer=printer, page=page, window=preview_win
            ),
        )
        print_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def _send_to_hardware(self, output_path: str, printer: str, page: str, window: tk.Toplevel):
        """
        Asynchronously dispatches the confirmed template target out to the physical spooler queue

        Args:
            output_path (str): Path to validated file template
            printer (str): Target device
            page (str): Page type to use
            window (tk.Toplevel): Root component, window in this case
        """

        window.destroy()
        self.status_lbl.config(
            text="Estado: Comunicandose con el dispositivo de impresion...",
            foreground="blue",
        )

        def print_worker():
            try:
                print_manager = PrintManager()
                file_extension = os.path.splitext(output_path)[1].lower()

                if file_extension == ".pdf":
                    print_manager.send_to_printer(
                        file_path=output_path, printer_name=printer, page_type=page
                    )
                elif file_extension == ".docx":
                    print_document_smart(file_path=output_path, printer_name=printer)
                else:
                    if os.path.exists(output_path):
                        print_manager.send_to_printer(
                            file_path=output_path, printer_name=printer, page_type=page
                        )

                self.root.after(0, self._handle_success)

            except exceptions.HardwareError as e:
                logger.exception("Critical fail occurred during print spooler transmission.")
                error_clean_msg = exceptions.translate_exception(e)
                self.root.after(0, lambda: self._handle_error(err_msg=error_clean_msg))

        hardware_thread = Thread(target=print_worker)
        hardware_thread.daemon = True
        hardware_thread.start()

    def _handle_success(self):
        self.action_btn.config(state="normal")
        self.status_lbl.config(
            text="Estado: ¡Operación completada con éxito en el hardware!",
            foreground="green",
        )
        messagebox.showinfo("Éxito", "El documento ha sido procesado e impreso de forma segura.")

    def _handle_error(self, err_msg: str):
        self.action_btn.config(state="normal")
        self.status_lbl.config(text="Estado: Error en la cola de impresión.", foreground="red")
        messagebox.showerror("Error de Procesamiento", f"Ocurrió un fallo: {err_msg}")


if __name__ == "__main__":
    logger.info("FastPrint application starting")
    root = tk.Tk()
    app = FastPrintApp(root)
    root.mainloop()
