import os
import sys


def send_to_system_printer(file_path: str) -> None:
    """
    Sends a processed file directly to the OS default print spooler

    Args:
        file_path (str): The absolute or relative to the file to be printed

    Raises:
        FileNotFoundError: If the specified file does not exists
        RunTimeError: If the print platform is unsupported or the OS operation fails.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"The file to print was not found at {file_path}")

    if sys.platform == "win32":
        try:
            os.startfile(filepath=file_path, operation="print")
        except Exception as e:
            raise RuntimeError(
                f"Windows print spooler failed to accept the file: {e}")
    else:
        raise RuntimeError(
            f"Unsupported operating system: {sys.platform}"
            f"Direct hardware printing is currently optimized for Windows"
        )
