#!/usr/bin/env bash

set -euo pipefail

# ------------------------------------------------------------
# image-export.sh
#
# Export 1 or more images into a 3200px-wide AVIF suitable
# for blog publishing.
#
# Supports grid layouts and single-image export.
#
# Requires:
#   - ImageMagick (magick)
#
# Output directory:
#   content/images/incoming/
#
# ------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DEFAULT_QUALITY=50
QUALITY=$DEFAULT_QUALITY
GRID=""
NAME=""
COLLECTION=""
OUTPUT_FILE=""

print_help() {
cat <<EOF
Usage:
  image-export.sh [options] image1 [image2 ...]

Description:
  Export one or more images as a 3200px-wide AVIF for blog use.
  Supports optional grid layouts.

Options:
  -g, --grid WxH       Grid layout (e.g. 3x2, 2x2, 4x1)
                       Number of images must equal W*H.

  -q, --quality N      AVIF quality (default: $DEFAULT_QUALITY)

  -n, --name NAME      Base output filename (without extension).
                       Default: timestamp.

  -c, --collection COLLECTION
                       Collection filename.
                       Default: incoming.

  -o, --output FILE    Explicit output path (overrides default dir).

  -h, --help           Show this help message.

Examples:
  image-export.sh photo.jpg

  image-export.sh -g 2x2 img1.jpg img2.jpg img3.jpg img4.jpg

  image-export.sh -g 4x1 -q 45 *.jpg
EOF
}

# ------------------------------------------------------------
# Parse options with getopt
# ------------------------------------------------------------

export PATH="/etc/profiles/per-user/jsteward/bin/:$PATH"

if ! OPTS=$(getopt -o g:q:n:c:o:h --long grid:,quality:,name:,collection:,output:,help -n 'image-export.sh' -- "$@"); then
    print_help
    exit 1
fi

eval set -- "$OPTS"

while true; do
    case "$1" in
        -g|--grid)
            GRID="$2"
            shift 2
            ;;
        -q|--quality)
            QUALITY="$2"
            shift 2
            ;;
        -n|--name)
            NAME="$2"
            shift 2
            ;;
        -c|--collection)
            COLLECTION="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        --)
            shift
            break
            ;;
        *)
            break
            ;;
    esac
done

# Remaining args = input images
if [ "$#" -lt 1 ]; then
    echo "Error: At least one input image is required."
    exit 1
fi

INPUTS=("$@")

# ------------------------------------------------------------
# Validate grid
# ------------------------------------------------------------

if [ -n "$GRID" ]; then
    if [[ ! "$GRID" =~ ^[0-9]+x[0-9]+$ ]]; then
        echo "Error: Grid must be in WxH format (e.g. 3x2)"
        exit 1
    fi

    WIDTH=${GRID%x*}
    HEIGHT=${GRID#*x}
    REQUIRED=$((WIDTH * HEIGHT))

    if [ "${#INPUTS[@]}" -ne "$REQUIRED" ]; then
        echo "Error: Grid $GRID requires $REQUIRED images, but ${#INPUTS[@]} provided."
        exit 1
    fi
fi

# ------------------------------------------------------------
# Determine output filename
# ------------------------------------------------------------

if [ -z "$OUTPUT_FILE" ]; then
    if [ -z "$NAME" ]; then
        NAME=$(date +"%Y%m%d-%H%M%S")
    fi

    if [ -z "$COLLECTION" ]; then
        COLLECTION=incoming
    fi

    OUTPUT_DIR="$SCRIPT_DIR/content/images/$COLLECTION"
    mkdir -p "$OUTPUT_DIR"

    OUTPUT_FILE="$OUTPUT_DIR/$NAME.avif"
fi

# ------------------------------------------------------------
# Processing
# ------------------------------------------------------------

if [ -z "$GRID" ] && [ "${#INPUTS[@]}" -eq 1 ]; then
    # Single image
    magick "${INPUTS[0]}" \
        -auto-orient \
        -resize 3200x3200\> \
        -strip \
        -quality "$QUALITY" \
        "$OUTPUT_FILE"

else
    # Grid layout

    if [ -z "$GRID" ]; then
        # If multiple images but no grid specified:
        # default to horizontal strip
        GRID="${#INPUTS[@]}x1"
    fi

    ROWS=${GRID%x*}
    ROW_WIDTH=$(( 3200 / $ROWS ))

    montage "${INPUTS[@]}" \
        -auto-orient \
        -tile "$GRID" \
        -geometry +0+0 \
        -resize ${ROW_WIDTH}x \
        -strip \
        -quality "$QUALITY" \
        "$OUTPUT_FILE"
fi

echo "✓ Exported to:"
echo "  $OUTPUT_FILE"
