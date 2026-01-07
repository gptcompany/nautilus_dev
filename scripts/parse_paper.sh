#!/bin/bash
# Parse academic paper PDF to Markdown using MinerU
# Usage: ./parse_paper.sh <paper.pdf> [output_dir]
#
# Features:
# - Layout-aware PDF parsing
# - LaTeX formula preservation
# - Table extraction (HTML)
# - Image extraction with descriptions
#
# Output structure:
#   output_dir/
#   ├── paper.md           # Main markdown content
#   ├── images/            # Extracted images
#   └── metadata.json      # Paper metadata

set -e

PDF_PATH="$1"
OUTPUT_DIR="${2:-/media/sam/1TB/nautilus_dev/docs/research/parsed}"

if [ -z "$PDF_PATH" ]; then
    echo "Usage: $0 <paper.pdf> [output_dir]"
    echo ""
    echo "Examples:"
    echo "  $0 paper.pdf"
    echo "  $0 /path/to/paper.pdf /custom/output"
    exit 1
fi

if [ ! -f "$PDF_PATH" ]; then
    echo "Error: File not found: $PDF_PATH"
    exit 1
fi

# Extract paper ID from filename
PAPER_NAME=$(basename "$PDF_PATH" .pdf)
PAPER_ID=$(echo "$PAPER_NAME" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
PAPER_OUTPUT_DIR="$OUTPUT_DIR/$PAPER_ID"

echo "=== MinerU PDF Parser ==="
echo "Input:  $PDF_PATH"
echo "Output: $PAPER_OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$PAPER_OUTPUT_DIR"

# Activate MinerU standalone venv (in academic_research repo)
source /media/sam/1TB/academic_research/.venv_mineru/bin/activate

# Run MinerU with pipeline backend (local, no API)
# -b pipeline: Uses local models only
# -m auto: Automatically detect text vs OCR mode
# -l en: English (change for other languages)
echo "Parsing PDF with MinerU (this may take a few minutes)..."
mineru -p "$PDF_PATH" -o "$PAPER_OUTPUT_DIR" -b pipeline -m auto -l en

# Check if output was created
if [ -f "$PAPER_OUTPUT_DIR"/*.md ] || [ -f "$PAPER_OUTPUT_DIR"/*/auto/*.md ]; then
    echo ""
    echo "✅ Parsing complete!"
    echo ""

    # Find and display the markdown file
    MD_FILE=$(find "$PAPER_OUTPUT_DIR" -name "*.md" -type f | head -1)
    if [ -n "$MD_FILE" ]; then
        echo "Markdown output: $MD_FILE"
        echo ""
        echo "=== First 50 lines ==="
        head -50 "$MD_FILE"

        # Count formulas
        FORMULA_COUNT=$(grep -c '\$' "$MD_FILE" 2>/dev/null || echo "0")
        echo ""
        echo "=== Statistics ==="
        echo "Lines: $(wc -l < "$MD_FILE")"
        echo "LaTeX formulas: ~$FORMULA_COUNT"
    fi
else
    echo "⚠️ No markdown output found. Check MinerU logs."
    ls -la "$PAPER_OUTPUT_DIR"
fi

echo ""
echo "Done."
