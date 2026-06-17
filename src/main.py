import tkinter as tk

from src.core.container import AppContainer
from src.ui.main_window import FastPrintApp
from src.utils.logger import logger


def main():
    """
    Application entry point. Initializes the IoC container and starts the GUI loop.
    """
    logger.info("FastPrint application starting...")

    # Bootstrap the dependency graph
    container = AppContainer(queue_timeout_seconds=60)

    # Initialize the UI framework
    root = tk.Tk()

    # Inject the fully resolved service into the application window
    root.app = FastPrintApp(root=root, print_service=container.print_service)

    root.mainloop()


if __name__ == "__main__":
    main()
