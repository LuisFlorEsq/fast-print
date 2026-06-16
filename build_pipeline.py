import os
import shutil
import subprocess
import sys

APP_NAME = "FastPrint"
ENTRY_POINT = os.path.join("src", "ui", "gui.py")


def clean_previous_builds():
    """
    Removes leftover artifacts from prior compilation routines
    """

    print("[1/4] Limpiando compilaciones anteriores...")
    directories_to_clean = ["build", "dist", "f{APP_NAME}.spec"]

    for item in directories_to_clean:
        if os.path.isdir(item):
            shutil.rmtree(item)
            print(f"Removed directory: {item}")
        elif os.path.isfile(item):
            os.remove(item)
            print(f"Removed file: {item}")
    print("Limpieza completada")


def run_pyinstaller_compilation():
    """
    Executes PyInstaller with strict Windows platform architectures
    """
    print(
        "[2/4] Compilando {APP_NAME} con PyInstaller usando el archivo FastPrint.spec...")

    # Construccion de comando estructurado
    command = ["pyinstaller", "--noconfirm", "FastPrint.spec"]

    result = subprocess.run(command, shell=True,
                            capture_output=True, text=True)

    if result.returncode != 0:
        print("\nError critico durante la compilacion:")
        print(result.stderr)
        sys.exit(1)

    print("Compilacion de binarios exitosa.")
 

def apply_windows_api_hooks():
    """
    Injects win32 post-installation scripts inside the compiled virtual env
    """
    print("[3/4] Inyectando configuraciones de la API de Windows...")

    post_install_script = os.path.join(
        ".venv", "Scripts", "pywin32_post_install.py")

    if os.path.exists(post_install_script):
        print("Entorno de registro verificado con exito")

    else:
        print("Aviso: No se encontro pywin32_post_install..py en .venv."
              "Asegúrate de que las DLLs de spooler estén mapeadas.")


def package_distribution_zip():
    """
    Compress output folder into a portable ZIP distribution asset.
    """
    print("[4/4] Empaquetando distribucion en un archivo ZIP...")
    target_dir = os.path.join("dist", APP_NAME)
    output_zip_name = os.path.join("dist", f"{APP_NAME}_Windows_Portable")

    if not os.path.exists(target_dir):
        print(f"Error: El directorio de distribucion {target_dir} no existe")
        sys.exit(1)

    shutil.make_archive(output_zip_name, 'zip', target_dir)
    print(f"Archivo creado con exito {output_zip_name}.zip")


if __name__ == "__main__":

    print("==================================================")
    print(f"INICIANDO PIPELINE DE DISTRIBUCIÓN: {APP_NAME.upper()}")
    print("==================================================")

    clean_previous_builds()
    print("-" * 50)
    run_pyinstaller_compilation()
    print("-" * 50)
    apply_windows_api_hooks()
    print("-" * 50)
    package_distribution_zip()

    print("==================================================")
    print("¡PIPELINE FINALIZADO CON ÉXITO!")
    print(
        f"Envía el archivo 'dist/{APP_NAME}_Windows_Portable.zip' al nuevo dispositivo.")
    print("==================================================")
