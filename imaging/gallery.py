# automatically scan photos for galleries
from PIL import Image
from pathlib import Path
from os.path import basename

from .thumbnailgen import gen_thumbnail


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

        max_width = 500 if width < height * 6 else 3200

        src = f'/images/gallery/{gallery_id}/{basename(file)}'
        thumb_src = gen_thumbnail(
            inputdir=inputdir,
            outputdir=outputdir,
            src=src,
            max_width=max_width,
            quality=45,
        )

        images.append({
            'full': src,
            'thumb': thumb_src,
            'width': width,
            'height': height,
        })

    print(f'>>> Done, added {len(images)} images')
    return images
