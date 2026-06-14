class FastPrintError(Exception):
    """Base exception for FastPrint."""

    pass


# ----------------------------
# Validation
# ----------------------------
class ValidationError(FastPrintError):
    """Raised when user input is invalid."""

    pass


# ----------------------------
# Processing
# ----------------------------
class ProcessingError(FastPrintError):
    """Base processing exception."""

    pass


class ImageProcessingError(ProcessingError):
    """Raised during image processing failures."""

    pass


class DocumentProcessingError(ProcessingError):
    """Raised during document processing failures."""

    pass


# ----------------------------
# Printing
# ----------------------------
class PrintError(FastPrintError):
    """Base printer exception."""

    pass


class PrinterNotFoundError(PrintError):
    """Target printer does not exist."""

    pass


class HardwareError(PrintError):
    """Printer hardware failure."""

    pass


class QueueTimeoutError(PrintError):
    """Printer queue stuck too long."""

    pass


class PrinterBusyError(PrintError):
    """Printer is busy or unavailable."""

    pass


def translate_exception(exc: Exception) -> str:
    """
    Analyzes a native system exception and tries to translate it into a user-readable message

    Args:
        exc (Exception): Exception captured on the child thread

    Returns:
        str: User ready message to use in messagebox component.
    """
    if isinstance(exc, (HardwareError, DocumentProcessingError, QueueTimeoutError)):
        return str(exc)

    msg = str(exc).lower()

    if "win32" in msg or "shellexecute" in msg:
        if "31" in msg:
            return (
                "Error de Hardware (31): El dispositivo seleccionado no responde o "
                "el visor predeterminado de Windows no soporta la redirección de impresión."
            )
        if "1155" in msg:
            return (
                "Error de Asociación (1155): No hay ninguna aplicación instalada "
                "en Windows configurada para abrir o procesar este tipo de archivo."
            )
        if "access is denied" in msg or "error 5" in msg:
            return "Error de Permisos (5): Windows denegó el acceso a la impresora."
        "Intenta ejecutar como Administrador."

        return f"Error en el subsistema de impresión de Windows: {str(exc)}"

    if isinstance(exc, FileNotFoundError):
        return "Archivo no encontrado:"
    f"El archivo o ruta especificada no existe en el disco duro.\n({str(exc)})"

    if isinstance(exc, ValueError):
        return f"Error en los datos del formulario: {str(exc)}"

    # General fallback for not tracked exceptions
    return f"Ocurrió un error inesperado en el hardware o procesamiento:\n{str(exc)}"
