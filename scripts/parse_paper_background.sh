#!/bin/bash
# Background PDF parsing with status tracking
# Usage: ./parse_paper_background.sh <paper.pdf> <paper_id>
#
# Creates:
#   docs/research/parsed/{paper_id}/.status   - parsing status
#   docs/research/parsed/{paper_id}/.log      - parsing log
#   docs/research/parsed/{paper_id}/.pid      - process ID
#
# Status values: started|completed|failed

set -e

PAPER_PATH="$1"
PAPER_ID="$2"

if [ -z "$PAPER_PATH" ] || [ -z "$PAPER_ID" ]; then
    echo "Usage: $0 <paper.pdf> <paper_id>"
    echo "Example: $0 papers/2021-russo-adaptive.pdf 2021-russo-adaptive"
    exit 1
fi

if [ ! -f "$PAPER_PATH" ]; then
    echo "Error: File not found: $PAPER_PATH"
    exit 1
fi

OUTPUT_DIR="/media/sam/1TB/nautilus_dev/docs/research/parsed/${PAPER_ID}"
STATUS_FILE="${OUTPUT_DIR}/.status"
LOG_FILE="${OUTPUT_DIR}/.log"
PID_FILE="${OUTPUT_DIR}/.pid"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if already running (with command verification to avoid PID reuse issues)
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        # Verify this is actually our process by checking command contains our output dir
        if ps -p "$OLD_PID" -o args= 2>/dev/null | grep -q "${PAPER_ID}"; then
            echo "Warning: Parsing already in progress (PID: $OLD_PID)"
            echo "Status: $(cat "$STATUS_FILE" 2>/dev/null || echo 'unknown')"
            exit 0
        fi
        # PID exists but is a different process - stale PID file, continue
        rm -f "$PID_FILE"
    fi
fi

# Write initial status
echo "started:$(date +%s):$(date -Iseconds)" > "$STATUS_FILE"
echo "=== MinerU Background Parser ===" > "$LOG_FILE"
echo "Paper: $PAPER_PATH" >> "$LOG_FILE"
echo "Output: $OUTPUT_DIR" >> "$LOG_FILE"
echo "Started: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Launch in background with nohup (survives logout)
# Note: Using proper quoting - variables are expanded by parent shell
nohup bash -c "
    source /media/sam/1TB/academic_research/.venv_mineru/bin/activate

    echo 'Activating MinerU venv...' >> \"${LOG_FILE}\"

    if mineru -p \"${PAPER_PATH}\" -o \"${OUTPUT_DIR}\" -b pipeline -m auto -l en >> \"${LOG_FILE}\" 2>&1; then
        echo \"completed:\$(date +%s):\$(date -Iseconds)\" > \"${STATUS_FILE}\"
        echo '' >> \"${LOG_FILE}\"
        echo \"Parsing completed successfully at \$(date)\" >> \"${LOG_FILE}\"

        # Extract formulas automatically - find the actual markdown file
        MARKDOWN_FILE=\"\"
        if [ -f \"${OUTPUT_DIR}/auto/${PAPER_ID}.md\" ]; then
            MARKDOWN_FILE=\"${OUTPUT_DIR}/auto/${PAPER_ID}.md\"
        elif [ -f \"${OUTPUT_DIR}/auto/\$(basename \"${PAPER_PATH}\" .pdf).md\" ]; then
            MARKDOWN_FILE=\"${OUTPUT_DIR}/auto/\$(basename \"${PAPER_PATH}\" .pdf).md\"
        else
            # Find any .md file in auto directory
            MARKDOWN_FILE=\$(find \"${OUTPUT_DIR}/auto\" -name \"*.md\" -type f 2>/dev/null | head -1)
        fi

        if [ -n \"\$MARKDOWN_FILE\" ] && [ -f \"\$MARKDOWN_FILE\" ]; then
            python /media/sam/1TB/nautilus_dev/scripts/extract_formulas.py \
                \"\$MARKDOWN_FILE\" \
                --output json > \"${OUTPUT_DIR}/.formulas.json\" 2>/dev/null || true
            echo \"Formulas extracted from \$MARKDOWN_FILE to .formulas.json\" >> \"${LOG_FILE}\"
        else
            echo 'Warning: No markdown file found for formula extraction' >> \"${LOG_FILE}\"
        fi
    else
        echo \"failed:\$(date +%s):\$(date -Iseconds)\" > \"${STATUS_FILE}\"
        echo '' >> \"${LOG_FILE}\"
        echo \"Parsing FAILED at \$(date)\" >> \"${LOG_FILE}\"
    fi

    # Cleanup PID file
    rm -f \"${PID_FILE}\"
" >> "$LOG_FILE" 2>&1 &

# Save PID
echo $! > "$PID_FILE"

echo "Background parsing started"
echo "  Paper ID: $PAPER_ID"
echo "  PID: $(cat "$PID_FILE")"
echo "  Status: $STATUS_FILE"
echo "  Log: $LOG_FILE"
echo ""
echo "Check status: cat $STATUS_FILE"
echo "Follow log: tail -f $LOG_FILE"
