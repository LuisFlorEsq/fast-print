import os
import sys
import tkinter as tk

from tkinter import ttk, filedialog, messagebox
from threading import Thread


from src.core.image import resize_image_to_cm, save_image_for_printing
from src.core.grid import create_grid_canvas
from src.core.document import extract_text_from_docx, convert_text_to_printable_images
from src.core.printer import send_to_system_printer, get_available_printers


from src.config import IMAGE_EXTENSIONS, DOC_EXTENSIONS


class FastPrintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fast Print Tool")
        self.root.geomertry("520x450")
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
        file_entry.pack(side=tk.LEFT, cx=5, expand=True, fill=tk.X)

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

        ttk.Label(dim_frame, text="Ancho (cm):").pack(side=tk.LEFT, cx=2)
        self.width_ent = ttk.Entry(dim_frame, width=8)
        self.width_ent.pack(side=tk.LEFT, cx=10)

        ttk.Label(dim_frame, text="Alto (cm):").pack(side=tk.LEFT, cx=2)
        self.height_ent = ttk.Entry(dim_frame, width=8)
        self.height_ent.pack(side=tk.LEFT, cx=10)

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
        self.grid_combo.pack(side=tk.LEFT, cx=10)

        # Row 3: Page Constraint Context
        page_frame = ttk.Frame(config_lf)
        page_frame.pack(fill=tk.X, pady=5)

        ttk.Label(page_frame, text="Tamaño de papel:").pack(side=tk.LEFT, cx=2)
        ttk.Radiobutton(page_frame, text="Carta (Letter)",
                        variable=self.page_type, value="letter").pack(side=tk.LEFT, cx=10)
        ttk.Radiobutton(page_frame, text="A4", variable=self.page_type,
                        value="a4").pack(side=tk.LEFT, cx=10)

        # ---------------------------------------------------------------------
        # SECTION 3: Hardware Print Routing
        # ---------------------------------------------------------------------
        hardware_lf = ttk.LabelFrame(
            main_frame, text="Enrutamiento de Hardware", padding=10)
        hardware_lf.pack(fill=tk.X, pady=(0, 20))

        print_chk = ttk.Checkbutton(
            hardware_lf, text="Enviar directo a la impresora", variable=self.is_print_enabled)
        print_chk.pack(side=tk.LEFT, cx=5)

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
