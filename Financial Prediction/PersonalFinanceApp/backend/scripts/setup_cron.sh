#!/bin/bash

# Setup script for ASX prediction cron job
# This script sets up a weekly cron job to update ASX stock predictions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$SCRIPT_DIR/update_asx_predictions.py"
LOG_FILE="$SCRIPT_DIR/asx_predictions_update.log"

echo "Setting up ASX prediction cron job..."

# Check if script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Make script executable
chmod +x "$PYTHON_SCRIPT"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Create a wrapper script that sets up the environment
WRAPPER_SCRIPT="$SCRIPT_DIR/run_asx_update.sh"
cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash

# Wrapper script for ASX prediction update
# This ensures proper environment setup

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT:\$PYTHONPATH"

# Run the prediction update script
python "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1

# Log completion
echo "\$(date): ASX prediction update completed" >> "$LOG_FILE"
EOF

chmod +x "$WRAPPER_SCRIPT"

# Create cron job entry (runs every Sunday at 2 AM)
CRON_JOB="0 2 * * 0 $WRAPPER_SCRIPT"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$WRAPPER_SCRIPT"; then
    echo "Cron job already exists. Updating..."
    # Remove existing entry
    crontab -l 2>/dev/null | grep -v "$WRAPPER_SCRIPT" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job setup complete!"
echo "The ASX prediction update will run every Sunday at 2:00 AM"
echo "Logs will be written to: $LOG_FILE"
echo ""
echo "To manually run the update:"
echo "  $WRAPPER_SCRIPT"
echo ""
echo "To view current cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -l | grep -v '$WRAPPER_SCRIPT' | crontab -" 