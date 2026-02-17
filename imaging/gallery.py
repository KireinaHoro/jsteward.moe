# automatically scan photos for galleries
from PIL import Image
from pathlib import Path


def image_getter(inputdir):
    return lambda gallery_id: get_images(inputdir, gallery_id)


def get_images(inputdir, gallery_id):
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
        images.append({
            'name': file.stem,
            'width': width,
            'height': height,
        })

    print(f'>>> Done, added {len(images)} images')
    return images
