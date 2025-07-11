#!/bin/bash

VENV_DIR="venv"
SCRIPT_NAME="program.py"
REQUIREMENTS_FILE="requirements.txt"
REQUIRED_PACKAGES="requests"

# Function to detect and install tkinter
install_tkinter() {
    echo "📦 Attempting to install tkinter for your distro..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        echo "⚠️ Could not detect OS. Please install tkinter manually."
        return
    fi

    case "$DISTRO" in
        ubuntu|debian)
            sudo apt-get update -qq
            sudo apt-get install -y python3-tk
            ;;
        fedora)
            sudo dnf install -y python3-tkinter
            ;;
        arch)
            sudo pacman -Sy --noconfirm tk
            ;;
        kali)
            sudo apt-get update -qq
            sudo apt-get install -y python3-tk
            ;;
        *)
            echo "❗ Distro $DISTRO not recognized. Install tkinter manually."
            ;;
    esac
}

# Step 1: Create venv if needed
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "✅ Virtual environment already exists."
fi

# Step 2: Activate venv
source $VENV_DIR/bin/activate

# Step 3: Create requirements.txt if not exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "📝 Creating requirements.txt..."
    echo "$REQUIRED_PACKAGES" > $REQUIREMENTS_FILE
fi

# Step 4: Install pip packages
echo "📥 Installing required packages..."
pip install --upgrade pip
pip install -r $REQUIREMENTS_FILE

# Step 5: Ensure tkinter is installed (may require sudo)
install_tkinter

# Step 6: Run the program
if [ -f "$SCRIPT_NAME" ]; then
    echo "🚀 Running $SCRIPT_NAME..."
    python $SCRIPT_NAME
else
    echo "❌ $SCRIPT_NAME not found."
fi
