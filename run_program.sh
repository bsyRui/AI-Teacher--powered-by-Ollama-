#!/bin/bash

VENV_DIR="venv"
SCRIPT_NAME="program.py"
REQUIREMENTS_FILE="requirements.txt"

# List of Python packages your program needs
REQUIRED_PACKAGES="requests"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "✅ Virtual environment already exists."
fi

# Activate virtual environment
source $VENV_DIR/bin/activate

# Create requirements.txt if missing
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "📝 Creating requirements.txt..."
    echo "$REQUIRED_PACKAGES" > $REQUIREMENTS_FILE
fi

echo "📥 Installing required packages..."
pip install --upgrade pip
pip install -r $REQUIREMENTS_FILE

# Ensure tkinter is available via system package manager
echo "📦 Ensuring python3-tk is installed (for tkinter)..."
sudo apt-get update -qq
sudo apt-get install -y python3-tk

# Run the program
if [ -f "$SCRIPT_NAME" ]; then
    echo "🚀 Running $SCRIPT_NAME..."
    python $SCRIPT_NAME
else
    echo "❌ $SCRIPT_NAME not found."
fi
