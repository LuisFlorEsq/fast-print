import os
import click

from src.core.image import resize_image_to_cm, save_image_for_printing


@click.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--width', '-w', type=float, help='Ancho en centímetros (cm).')
@click.option('--height', '-h', type=float, help='Alto en centímetros (cm).')
@click.option('--dpi', default=300, help='DPI de la impresora (Por defecto 300).')
@click.option('--output', '-o', type=click.Path(), help='Ruta de guardado personalizada.')
def main(filepath, width, height, dpi, output):
    """Fast Print CLI: Herramienta ultra-ligera para preparar archivos de impresión."""
    try:
        processed_img = resize_image_to_cm(
            filepath, width_cm=width, height_cm=height, dpi=dpi)

        if not output:
            base, ext = os.path.splitext(filepath)
            output = f"{base}_print{ext}"

        save_image_for_printing(processed_img, output, dpi=dpi)
        click.secho(
            f"Procesado con éxito. Archivo listo en: {output}", fg="green")

    except Exception as e:
        click.secho(f"Error interno en el procesamiento: {e}", fg="red")


if __name__ == '__main__':
    main()
