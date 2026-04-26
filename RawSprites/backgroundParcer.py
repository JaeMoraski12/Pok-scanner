"""
composite_images.py

Pastes a single sprite image onto every background image in a folder
at a fixed (x, y) pixel coordinate.

Usage:
    python composite_images.py \
        --backgrounds ./backgrounds \
        --sprites ./sprites \
        --output ./output \

Arguments:
    --backgrounds   Path to folder containing background images
    --sprites        Path to the sprite image file
    --num-var       Number of variations for each sprite background pair.
    --output        Path to folder where composited images will be saved
"""

import argparse
import sys
import random
from pathlib import Path
from PIL import Image

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}

minCoord = (140,65)
maxCoord = (216,33)

cropRegion = 


def parse_args():
    parser = argparse.ArgumentParser(
        description="Paste a sprite onto all background images at a fixed (x, y) position."
    )
    parser.add_argument(
        "--backgrounds", required=True, type=Path,
        help="Folder containing background images"
    )
    parser.add_argument(
        "--sprites", required=True, type=Path,
        help="Folder to sprites"
    )
    parser.add_argument(
        "--num-var", required=True, type=int,
        help="How many variations of the image for each combiniaton"
    )
    parser.add_argument(
        "--output", required=True, type=Path,
        help="Folder to save composited images"
    )
    return parser.parse_args()

def load_image(image_path: Path) -> Image.Image:
    if not image_path.is_file():
        print(f"Error: Sprite file not found: {image_path}")
        sys.exit(1)
    sprite = Image.open(image_path).convert("RGBA")
    print(f"Loaded sprite: {image_path.name} ({sprite.width}x{sprite.height})")
    return sprite


def get_image_files(bg_folder: Path) -> list[Path]:
    if not bg_folder.is_dir():
        print(f"Error: Backgrounds folder not found: {bg_folder}")
        sys.exit(1)
    files = sorted([
        f for f in bg_folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ])
    if not files:
        print(f"Error: No supported image files found in: {bg_folder}")
        sys.exit(1)
    print(f"Found {len(files)} background image(s) in '{bg_folder}'")
    return files




def composite(bg_path: Path, sprite_path: Path, output_folder: Path):
    bg = load_image(bg_path)
    sprite = load_image(sprite_path)

    x = random.randint(minCoord[0],maxCoord[0]) - (sprite.width // 2)
    y = random.randint(maxCoord[1],minCoord[1]) - (sprite.height // 2)

    # Warn if sprite would be clipped by background bounds
    if x + sprite.width > bg.width or y + sprite.height > bg.height:
        print(f"  Warning: sprite extends beyond background bounds for '{bg_path.name}'")
    if x < 0 or y < 0:
        print(f"  Warning: negative coordinates may crop the sprite for '{bg_path.name}'")

    result = bg.copy()
    result.paste(sprite, (x, y), sprite)
    result.crop()

    out_path = output_folder / bg_path.name

    # Save as PNG to avoid re-compression artefacts; preserve original ext for JPEGs
    if bg_path.suffix.lower() in {".jpg", ".jpeg"}:
        result.save(out_path, "JPEG", quality=95)
    else:
        result.save(out_path)

    print(f"  Saved → {out_path}")


def main():
    args = parse_args()

    sprites = get_image_files(args.sprites)
    bg_files = get_image_files(args.backgrounds)

    args.output.mkdir(parents=True, exist_ok=True)
    print(f"Output folder: {args.output}\n")

    for bg_path in bg_files:
        for sprite_path in sprites:
            out_path = args.output / sprite_path.name
            out_path.mkdir(parents=True, exist_ok=True)
            composite(bg_path, sprite_path, out_path)

    print(f"\nDone! {len(bg_files)} image(s) saved to '{args.output}'")


if __name__ == "__main__":
    main()