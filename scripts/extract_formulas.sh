#!/bin/bash
# Extract numbered equations from PDF (minimal token usage)
# Usage: ./extract_formulas.sh paper.pdf [equation_number]
#
# Examples:
#   ./extract_formulas.sh paper.pdf          # List all equations
#   ./extract_formulas.sh paper.pdf 2.1      # Extract equation 2.1

PDF="$1"
EQ_NUM="$2"

if [ -z "$PDF" ]; then
    echo "Usage: $0 <paper.pdf> [equation_number]"
    exit 1
fi

if [ ! -f "$PDF" ]; then
    echo "Error: File not found: $PDF"
    exit 1
fi

# Extract text
TEXT=$(pdftotext "$PDF" - 2>/dev/null)

if [ -z "$EQ_NUM" ]; then
    # List all equation numbers
    echo "=== Equations found in $(basename "$PDF") ==="
    echo "$TEXT" | grep -oE '\([0-9]+\.[0-9]+\)' | sort -u | head -30
else
    # Extract specific equation with context
    echo "=== Equation ($EQ_NUM) ==="
    NEXT_NUM=$(echo "$EQ_NUM" | awk -F. '{print $1"."($2+1)}')
    echo "$TEXT" | awk "/^\($EQ_NUM\)/,/^\($NEXT_NUM\)/" | head -5 | tr '\n' ' '
    echo ""
fi
