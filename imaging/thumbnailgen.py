from pathlib import Path
from PIL import Image


def gen_thumbnail(
    inputdir: Path,
    outputdir: Path,
    src: str,
    max_width: int,
    quality: int = 50,
) -> str:
    """
    Ensure a resized AVIF version exists in the output directory.

    Parameters:
        inputdir  - Pelican PATH (content root)
        outputdir - Pelican OUTPUT_PATH
        src       - image src relative to site root (e.g. /images/foo.avif)
        max_width - max width of generated image
        quality   - AVIF encoding quality (lower = smaller)

    Returns:
        New src path (relative to site root)
    """

    # Remove leading slash if present
    rel_src = src.lstrip("/")

    input_path = inputdir / rel_src
    output_path = outputdir / rel_src

    if not input_path.exists():
        raise FileNotFoundError(f"Missing source image: {input_path}")

    # Build resized filename
    stem = input_path.stem
    resized_name = f"{stem}-{max_width}.avif"

    resized_rel = str(Path(rel_src).with_name(resized_name))
    resized_output_path = outputdir / resized_rel

    print(f'... {src} -> {resized_rel}')

    # If already exists, don’t regenerate
    if resized_output_path.exists():
        return "/" + resized_rel

    resized_output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_path) as im:
        width, height = im.size

        if width <= max_width:
            # Just copy original
            im.save(resized_output_path, format="AVIF", quality=quality)
        else:
            ratio = max_width / width
            new_height = int(height * ratio)

            resized = im.resize((max_width, new_height), Image.LANCZOS)
            resized.save(resized_output_path, format="AVIF", quality=quality)

    return "/" + resized_rel
