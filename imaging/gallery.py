# automatically scan photos for galleries
from PIL import Image
from pathlib import Path
from os.path import basename

from .thumbnailgen import gen_thumbnail, thumbnail_dimensions


def image_getter(inputdir, outputdir):
    return lambda gallery_id: get_images(
            inputdir=Path(inputdir),
            outputdir=Path(outputdir),
            gallery_id=gallery_id)


def get_images(inputdir, outputdir, gallery_id):
    print(f'>>> Scanning images for gallery {gallery_id}...')

    base_path = Path(inputdir) / 'images' / 'gallery' / gallery_id
    if not base_path.exists():
        print(f'!!! Gallery path {base_path} does not exist!')
        sys.exit(1)

    images = []

    for file in sorted(base_path.glob("*.avif")):
        try:
            with Image.open(file) as img:
                width, height = img.size
        except Exception as e:
            print(f'!!! failed to open {file}: {e}; skipping...')
            continue

        print(f'... {file} ({width} x {height})')

        src = f'/images/gallery/{gallery_id}/{basename(file)}'
        is_wide = width > height * 6
        thumb_widths = [3200] if is_wide else [320, 500]
        default_thumb_width = thumb_widths[-1]
        thumb_width, thumb_height = thumbnail_dimensions(
            width, height, default_thumb_width)

        thumbs = []
        for thumb_max_width in thumb_widths:
            thumb_src = gen_thumbnail(
                inputdir=inputdir,
                outputdir=outputdir,
                src=src,
                max_width=thumb_max_width,
                quality=45,
            )
            generated_width, _ = thumbnail_dimensions(
                width, height, thumb_max_width)
            thumbs.append({
                'src': thumb_src,
                'width': generated_width,
            })

        images.append({
            'full': src,
            'thumb': thumbs[-1]['src'],
            'thumb_srcset': ', '.join(
                f"{thumb['src']} {thumb['width']}w" for thumb in thumbs),
            'thumb_width': thumb_width,
            'thumb_height': thumb_height,
            'width': width,
            'height': height,
        })

    print(f'>>> Done, added {len(images)} images')
    return images
