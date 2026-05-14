# automatically scan photos for galleries
import sys
import re

from PIL import ExifTags, Image
from pathlib import Path
from os.path import basename

from .thumbnailgen import gen_thumbnail, thumbnail_dimensions


def _format_number(value):
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)

    if value.is_integer():
        return str(int(value))

    return f'{value:.1f}'.rstrip('0').rstrip('.')


def _exif_value(exif, ifd, *names):
    try:
        values = exif if ifd is None else exif.get_ifd(ifd)
    except Exception:
        return None

    for tag_id, value in values.items():
        if ExifTags.TAGS.get(tag_id, tag_id) in names:
            return value
    return None


def _gallery_alt(exif):
    if not exif:
        return None

    exif_ifd = ExifTags.IFD.Exif
    camera = ' '.join(
        str(part).strip()
        for part in (
            _exif_value(exif, None, 'Make'),
            _exif_value(exif, None, 'Model'),
        )
        if part
    )
    lens = ' '.join(
        str(part).strip()
        for part in (
            _exif_value(exif, exif_ifd, 'LensMake'),
            _exif_value(exif, exif_ifd, 'LensModel'),
        )
        if part
    )

    focal_length = _format_number(_exif_value(exif, exif_ifd, 'FocalLength'))
    focal_length = f'{focal_length}mm' if focal_length else None

    aperture = _format_number(_exif_value(exif, exif_ifd, 'FNumber'))
    aperture = f'f/{aperture}' if aperture else None

    shutter_speed = _exif_value(exif, exif_ifd, 'ExposureTime')
    if shutter_speed:
        try:
            seconds = float(shutter_speed)
            if seconds < 1:
                shutter_speed = f'1/{round(1 / seconds)}s'
            else:
                shutter_speed = f'{_format_number(seconds)}s'
        except (TypeError, ValueError):
            shutter_speed = f'{shutter_speed}s'

    iso = _exif_value(
        exif,
        exif_ifd,
        'ISOSpeedRatings',
        'PhotographicSensitivity',
    )
    iso = f'ISO {_format_number(iso)}' if iso else None

    exposure = ' '.join(
        part for part in (aperture, shutter_speed, iso) if part)
    lines = [
        ' | '.join(part for part in (camera, lens) if part),
        ' | '.join(part for part in (focal_length, exposure) if part),
    ]
    lines = [line for line in lines if line]
    return '\n'.join(lines) if lines else None


def image_getter(inputdir, outputdir):
    return lambda gallery_id, limit=None: get_images(
            inputdir=Path(inputdir),
            outputdir=Path(outputdir),
            gallery_id=gallery_id,
            limit=limit)


def category_getter(inputdir):
    return lambda: get_categories(Path(inputdir))


def get_categories(inputdir):
    gallery_path = Path(inputdir) / 'images' / 'gallery'
    categories = []

    for path in sorted(gallery_path.iterdir()):
        if path.name.startswith('.') or not path.is_dir():
            continue
        if not list(path.glob('*.avif')):
            continue

        slug = re.sub(r'^\d+-', '', path.name)
        categories.append({
            'id': path.name,
            'slug': slug,
            'title': slug.replace('-', ' ').title(),
            'url': f'/gallery_{slug}.html',
        })

    return categories


def get_images(inputdir, outputdir, gallery_id, limit=None):
    print(f'>>> Scanning images for gallery {gallery_id}...')

    base_path = Path(inputdir) / 'images' / 'gallery' / gallery_id
    if not base_path.exists():
        print(f'!!! Gallery path {base_path} does not exist!')
        sys.exit(1)

    images = []

    for file in sorted(base_path.glob("*.avif"))[:limit]:
        try:
            with Image.open(file) as img:
                width, height = img.size
                alt = _gallery_alt(img.getexif())
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
            'alt': alt,
        })

    print(f'>>> Done, added {len(images)} images')
    return images
