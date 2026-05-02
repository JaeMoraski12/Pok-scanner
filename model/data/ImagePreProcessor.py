#!/usr/bin/env python3

import argparse
import random
from pathlib import Path
from PIL import Image

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in VALID_EXTENSIONS


def augment_image(
    img: Image.Image,
    max_rotation: float,
    max_translate_x: int,
    max_translate_y: int,
    image_size: int,
    fill_color=(0, 0, 0),
) -> Image.Image:
    """
    Apply a small random rotation and translation to an image.
    Keeps the original image size.
    """
    angle = random.uniform(-max_rotation, max_rotation)
    tx = random.randint(-max_translate_x, max_translate_x)
    ty = random.randint(-max_translate_y, max_translate_y)

    # Rotate first
    rotated = img.rotate(
        angle,
        resample=Image.Resampling.BICUBIC,
        expand=False,
        fillcolor=fill_color,
    )

    # Then translate using affine transform
    translated = rotated.transform(
        rotated.size,
        Image.Transform.AFFINE,
        (1, 0, tx, 0, 1, ty),
        resample=Image.Resampling.BICUBIC,
        fillcolor=fill_color,
    )

    # Then crop and resize to ensure the final image is the desired size
    width, height = translated.size

    # Example: Convert to 1:1 (Square)
    new_ratio = 1.0
    new_width = min(width, int(height * new_ratio))
    new_height = min(height, int(width / new_ratio))

    # Calculate coordinates for cropping
    left = (width - new_width) / 2
    top = (height - new_height) / 2
    right = (width + new_width) / 2
    bottom = (height + new_height) / 2

    # Crop and then resize
    crop = translated.crop((left, top, right, bottom))
    resize = crop.resize((image_size, image_size)) # Final resize
    return resize


def get_fill_color(img: Image.Image):
    """
    Pick a reasonable fill color depending on image mode.
    """
    if img.mode == "RGBA":
        return (0, 0, 0, 0)
    if img.mode == "RGB":
        return (0, 0, 0)
    if img.mode == "L":
        return 0
    return 0


def save_image(img: Image.Image, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # JPEG does not support alpha
    if output_path.suffix.lower() in {".jpg", ".jpeg"} and img.mode == "RGBA":
        img = img.convert("RGB")

    img.save(output_path)


def process_directory(
    input_dir: Path,
    output_dir: Path,
    copies_per_image: int,
    max_rotation: float,
    max_translate_x: int,
    max_translate_y: int,
    image_size: int,
    preserve_structure: bool,
):
    image_paths = [p for p in input_dir.rglob("*") if p.is_file() and is_image_file(p)]

    if not image_paths:
        print("No image files found.")
        return

    print(f"Found {len(image_paths)} images.")

    for img_path in image_paths:
        try:
            with Image.open(img_path) as img:
                img.load()

                fill_color = get_fill_color(img)

                if preserve_structure:
                    relative_parent = img_path.parent.relative_to(input_dir)
                    target_dir = output_dir / relative_parent
                else:
                    target_dir = output_dir

                # Save original too if you want a full dataset copy:
                original_name = f"{img_path.stem}_orig{img_path.suffix.lower()}"
                cropped_original = augment_image(img, 0, 0, 0, image_size, fill_color)  # Just crop and resize original
                save_image(cropped_original, target_dir / original_name)

                for i in range(copies_per_image):
                    aug_img = augment_image(
                        img=img,
                        max_rotation=max_rotation,
                        max_translate_x=max_translate_x,
                        max_translate_y=max_translate_y,
                        image_size=image_size,
                        fill_color=fill_color,
                    )

                    output_name = f"{img_path.stem}_aug_{i+1}{img_path.suffix.lower()}"
                    output_path = target_dir / output_name
                    save_image(aug_img, output_path)

            print(f"Processed: {img_path}")

        except Exception as e:
            print(f"Skipped {img_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Create augmented copies of images with slight rotation and translation."
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing source images")
    parser.add_argument("output_dir", type=Path, help="Directory to save augmented images")
    parser.add_argument(
        "--copies",
        type=int,
        default=3,
        help="Number of augmented copies to create per image (default: 3)",
    )
    parser.add_argument(
        "--max-rotation",
        type=float,
        default=8.0,
        help="Maximum absolute rotation in degrees (default: 8.0)",
    )
    parser.add_argument(
        "--max-translate-x",
        type=int,
        default=10,
        help="Maximum horizontal translation in pixels (default: 10)",
    )
    parser.add_argument(
        "--max-translate-y",
        type=int,
        default=10,
        help="Maximum vertical translation in pixels (default: 10)",
    )
    parser.add_argument(
        "--flatten",
        action="store_true",
        help="Do not preserve input subdirectory structure in the output directory",
    )
    parser.add_argument(
        "--img-size",
        type=int,
        default=500,
        help="Resize images to this size (default: 500)",
    )

    args = parser.parse_args()

    if not args.input_dir.exists() or not args.input_dir.is_dir():
        raise ValueError(f"Input directory does not exist or is not a directory: {args.input_dir}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    process_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        copies_per_image=args.copies,
        max_rotation=args.max_rotation,
        max_translate_x=args.max_translate_x,
        max_translate_y=args.max_translate_y,
        image_size=args.img_size,
        preserve_structure=not args.flatten,
    )


if __name__ == "__main__":
    main()