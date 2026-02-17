from markdown.treeprocessors import Treeprocessor
from markdown.extensions import Extension
from xml.etree import ElementTree as ET
from pathlib import Path
from PIL import Image

from .thumbnailgen import gen_thumbnail


class PhotoSwipeImageProcessor(Treeprocessor):
    def __init__(self, md, inputdir, outputdir):
        super().__init__(md)
        self.inputdir = Path(inputdir)
        self.outputdir = Path(outputdir)

    def run(self, root):
        print(f'>>> Scanning images for article...')

        # Collect all images first
        images = []
        for parent in root.iter():
            for child in list(parent):
                if child.tag == "img":
                    images.append((parent, child))

        for parent, img in images:
            src = img.get("src")
            if not src:
                continue

            # Skip if already wrapped in <a>
            if parent.tag == "a":
                continue

            image_path = self.inputdir / src.lstrip("/")
            if not image_path.exists():
                continue

            try:
                with Image.open(image_path) as im:
                    width, height = im.size
            except Exception:
                continue

            # Create anchor
            a = ET.Element("a", {
                "href": src,
                "data-pswp-width": str(width),
                "data-pswp-height": str(height),
                "target": "_blank",
            })
            print(f'... {src} ({width} x {height})')

            index = list(parent).index(img)
            parent.remove(img)
            parent.insert(index, a)

            thumb_src = gen_thumbnail(
                inputdir=self.inputdir,
                outputdir=self.outputdir,
                src=src,
                max_width=1600,
                quality=50,
            )
            img.set('src', thumb_src)

            a.append(img)


class PhotoSwipeImageExtension(Extension):
    def __init__(self, inputdir, outputdir):
        super().__init__()
        self.inputdir = inputdir
        self.outputdir = outputdir

    def extendMarkdown(self, md):
        md.treeprocessors.register(
            PhotoSwipeImageProcessor(md, self.inputdir, self.outputdir),
            "photoswipe_images",
            15,
        )
