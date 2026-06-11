class FastPrintException(Exception):
    """Configure the base for all the exceptions on FastPrint application"""
    pass


class HardwareError(FastPrintException):
    """Launches when the physical printer or the Windows spooler reports an error"""
    pass


class DocumentProcessingError(FastPrintException):
    """Launches when a file (Image, PDF, DOCX ) fails during preparation or rendering"""
    pass


class DeviceTimeoutError(FastPrintException):
    """Launches when the printer queue jobs reach the time limit"""
    pass


def translate_exception(exc: Exception) -> str:
    """
    Analyzes a native system exception and tries to translate it into a user-readable message

    Args:
        exc (Exception): Exception captured on the child thread

    Returns:
        str: User ready message to use in messagebox component.
    """
    if isinstance(exc, (HardwareError, DocumentProcessingError, DeviceTimeoutError)):
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
            return "Error de Permisos (5): Windows denegó el acceso a la impresora. Intenta ejecutar como Administrador."

        return f"Error en el subsistema de impresión de Windows: {str(exc)}"

    if isinstance(exc, FileNotFoundError):
        return f"Archivo no encontrado: El archivo o ruta especificada no existe en el disco duro.\n({str(exc)})"

    if isinstance(exc, ValueError):
        return f"Error en los datos del formulario: {str(exc)}"

    # General fallback for not tracked exceptions
    return f"Ocurrió un error inesperado en el hardware o procesamiento:\n{str(exc)}"
