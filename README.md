# Fast Print Tool

A lightweight CLI and automation tool designed to prepare images and documents for printing without the overhead of heavy office suites. Optimized specifically for low-specification and legacy hardware.

## Features

- **Exact Physical Resizing**: Convert centimeters (cm) to exact pixel dimensions using embedded DPI metadata.
- **N-up Grid Layouts**:   Combine multiple images or copies into automated 2, 4, 6, or 8-up grids on standard page sizes (Letter/A4).
- **Resource Efficient**: Built on top of Python's `Pillow` and managed via `uv` for minimal CPU and RAM footprints.
- **Decoupled Architecture**: Pure core logic independent of the interface, ready for a lightweight Tkinter GUI in the future.

## Tech Stack

- **Language**: Python 3.11+
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (High-performance package installer written in Rust)
- **Core Dependencies**: Pillow (Image Processing), Click (CLI Framework)

## Project Structure

```text
fast-printer/
├── pyproject.toml         # Managed by uv
├── README.md
└── src/
    ├── cli.py             # Application Entry Point (CLI)
    └── core/              # Immutable Core Engine
        ├── __init__.py
        ├── image.py       # Centimeter scaling & DPI operations
        └── grid.py        # Canvas geometry & N-up calculations
```

## Installation & SetUp

Since this project uses `uv`, you dont need to manage virtual environments manually

1. Clone or navigate to the repository directory
2. Initialize and download dependencies instantly:

```bash
uv sync
```

## Usage Examples

Since this project is managed via `uv`, you can execute the CLI tool directly from the project root without manually activating any virtual environment. `uv run` will handle the high-performance execution context automatically.

### 1. Resize a Single Image to Physical Dimensions (cm)

To resize an image to a specific physical width (e.g., 15 cm) for printing. The height will be automatically calculated to maintain the original aspect ratio at a crisp 300 DPI:

```bash
uv run python -m src.ui.cli path/to/image.jpg --width 15
```

If you need to force an exact bounding box size (e.g., a square 10x10 cm photo) and save it with a custom output name:

```bash
uv run python -m src.ui.cli path/to/input.png -w 10 -h 10 -o custom_output.png
```