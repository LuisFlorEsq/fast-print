import os
import click
from PIL import Image

from src.core.image import resize_image_to_cm, save_image_for_printing
from src.core.grid import create_grid_canvas

from src.core.document import extract_text_from_docx, convert_text_to_printable_images
from src.core.printer import send_to_system_printer, get_available_printers

from src.config import IMAGE_EXTENSIONS, DOC_EXTENSIONS


@click.command()
@click.argument('path', type=click.Path(exists=True), required=False)
@click.option('--width', '-w', type=float, help='Ancho en centímetros (cm).')
@click.option('--height', '-h', type=float, help='Alto en centímetros (cm).')
@click.option('--grid', '-g', type=int, help='Numero de espacios en la cuadricula (ej. 2, 4, 6)')
@click.option('--page-type', default='letter', type=click.Choice(['letter', 'a4']), help='Tipo de pagina para la cuadricula')
@click.option('--dpi', default=300, help='DPI de la impresora (Por defecto 300).')
@click.option('--output', '-o', type=click.Path(), help='Ruta de guardado personalizada.')
@click.option('--print', '-p', 'print_now', is_flag=True, default=False, help='Manda el archivo directamente a la impresora fisica.')
@click.option('--printer', '-d', type=str, help='Nombre de la impresora específica a usar (Device).')
@click.option('--list-printers', is_flag=True, default=False, help='Muestra todas las impresoras configuradas en Windows.')
def main(path, width, height, grid, page_type,  dpi, output, print_now, printer, list_printers):
    """Fast Print CLI: Herramienta ultra-ligera para preparar archivos de impresión."""
    try:

        if list_printers:
            printers = get_available_printers()
            click.secho(
                "\nImpresoras instaladas detectadas en Windows 11:", fg="cyan", bold=True)
            for idx, p_name in enumerate(printers, 1):
                click.echo(f" {idx}. {p_name}")
            click.echo("")
            return

        if not path:
            raise click.UsageError(
                "Falta el argumento de ruta del archivo o carpeta.")

        # =====================================================================
        # CASE 1: DIRECT DOCUMENT PROCESSING (.pdf / .docx)
        # =====================================================================
        if path.lower().endswith(DOC_EXTENSIONS):
            click.echo(
                f"Procesando documento en segundo plano sin abrir aplicaciones pesadas: {os.path.basename(path)}")

            # SubCase A: Direct PDF printing
            if path.lower().endswith('.pdf') and not grid:
                if print_now:
                    click.echo(
                        f"Enviando PDF original directamente al spooler de hardware...")
                    send_to_system_printer(
                        file_path=path, printer_name=printer, watch_status=True)
                    click.secho(
                        f"¡PDF enviado e impreso con éxito!.", fg="green")
                else:
                    click.secho(
                        f"El procesamiento del PDF individual require la bandera --print (-p) para enviarse directamente", fg="yellow")

                return

            # SubCase B: Word Document processing (.docx) text to layout converter
            elif path.lower().endswith('.docx'):
                text_content = extract_text_from_docx(file_path=path)
                pages = convert_text_to_printable_images(
                    text=text_content, dpi=dpi)

                click.echo(
                    f"Documento convertido a {len(pages)} páginas(s) de imagen ligera en RAM")

                if grid:
                    click.echo(
                        f"Aplicando cuadricula {grid}-up a las páginas del documento...")
                    grid_canvas = create_grid_canvas(
                        pages, grid_size=grid, page_type=page_type, dpi=dpi)
                    final_output = output if output else f"{os.path.splitext(path)[0]}_grid_print.png"
                    save_image_for_printing(grid_canvas, final_output, dpi=dpi)

                    if print_now:
                        send_to_system_printer(
                            file_path=final_output, printer_name=printer, watch_status=True)
                    click.secho(
                        f"Cuadricula de Word completada en: {final_output}", fg="green")

                else:
                    # Print pages individually
                    for idx, page_img in enumerate(pages, 1):
                        final_output = output if output else f"{os.path.splitext(path)[0]}_page_{idx}.png"
                        save_image_for_printing(
                            img=page_img, output_path=final_output, dpi=dpi)
                        if print_now:
                            send_to_system_printer(
                                file_path=final_output, printer_name=printer, watch_status=True)
                    click.secho(
                        f"Páginas de Word impresas/guardadas de forma limpia.", fg="green")

                return

        # =====================================================================
        # CASE 2: PROCESSING A FOLDER (Grid-Multi for images)
        # =====================================================================

        elif os.path.isdir(path):
            if not grid:
                raise click.UsageError(
                    "Al procesar una carpeta, debes espicificar el tamaño de la cuadricula usando --grid.")

            click.echo(f"Escaneando carpeta de forma ligera: {path}")

            # Get all valid images in the directory
            file_list = [
                os.path.join(path, f) for f in os.listdir(path)
                if f.lower().endswith(IMAGE_EXTENSIONS)
            ]

            if not file_list:
                click.secho(
                    "No se encontraron imágenes compatibles en la carpeta.", fg="yellow")
                return

            click.echo(
                f"Se encontraron {len(file_list)} imágenes. Generando páginas de cuadrícula...")

            # Process files in chunks matching the grid size
            page_number = 1
            for i in range(0, len(file_list), grid):
                chunk_paths = file_list[i:i + grid]

                # Lazy load images
                chunk_images = [Image.open(p) for p in chunk_paths]
                grid_canvas = create_grid_canvas(
                    images=chunk_images, grid_size=grid, page_type=page_type, dpi=dpi)

                # Determine output path for each generated page
                out_dir = output if output else path
                out_name = f"grid_page_{page_number}_{page_type}.png"
                final_output = os.path.join(out_dir, out_name)

                save_image_for_printing(
                    img=grid_canvas, output_path=final_output, dpi=dpi)
                click.echo(f"Pagina {page_number} guardada: {out_name}")

                # Native silent printer if triggered
                if print_now:
                    send_to_system_printer(
                        file_path=final_output, printer_name=printer, watch_status=True)

                # Close images to free memory buffers
                for img in chunk_images:
                    img.close()
                page_number += 1

            click.secho(f"Proceso por lotes completado con éxito", fg="green")

        # =====================================================================
        # CASE 3: PROCESSING A SINGLE IMAGE FILE
        # =====================================================================
        else:

            final_output = output

            # Subcase A: Single File Grid (Duplicate an image into N slots)
            if grid:
                click.echo(
                    f"Duplicando imagen en cuadricula {grid}-up: {os.path.basename(path)}")

                with Image.open(path) as single_img:
                    images_batch = [single_img] * grid
                    grid_canvas = create_grid_canvas(
                        images=images_batch, grid_size=grid, page_type=page_type, dpi=dpi)

                if not final_output:
                    base, ext = os.path.splitext(path)
                    final_output = f"{base}_grid_{grid}{ext}"

                save_image_for_printing(
                    img=grid_canvas, output_path=output, dpi=dpi)
                click.secho(
                    f"Cuadricula guardara con éxito en: {output}", fg="green")

            # Subcase B: Standard Single Image Resizing

            elif width or height:
                processed_img = resize_image_to_cm(
                    input_path=path, width_cm=width, height_cm=height, dpi=dpi)

                if not final_output:
                    base, ext = os.path.splitext(path)
                    final_output = f"{base}_print{ext}"

                save_image_for_printing(
                    img=processed_img, output_path=output, dpi=dpi)
                click.secho(
                    f"Imagen redimensionada con éxito en {output}", fg="green")

            else:
                raise click.UsageError(
                    "Debes especificar dimensiones (--width/--height) o una cuadricula (--grid)")

            if print_now:
                send_to_system_printer(
                    file_path=output, printer_name=printer, watch_status=True)
                click.secho(
                    f"¡Impresión física completada correctamente en el hardware!", fg="cyan")

    except Exception as e:
        click.secho(f"Error interno en el procesamiento: {e}", fg="red")


if __name__ == '__main__':
    main()
