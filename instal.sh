#!/bin/bash

echo "Installing Credit Copyright Manager..."

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
CREDIT_PATH="${SCRIPT_DIR}/credit.py"

if [ ! -f "$CREDIT_PATH" ]; then
    echo "Error: credit.py not found in the current directory."
    exit 1
fi

chmod +x "$CREDIT_PATH"

if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Creating symlink in /usr/local/bin..."
    sudo ln -sf "$CREDIT_PATH" /usr/local/bin/credit
    
    if [ $? -eq 0 ]; then
        echo "Success! You can now run 'credit' from anywhere."
    else
        echo "Failed to create symlink. You may need administrator privileges."
        echo "Try running: sudo ln -sf \"$CREDIT_PATH\" /usr/local/bin/credit"
    fi
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Creating batch file..."
    BATCH_PATH="$SCRIPT_DIR/credit.bat"
    
    echo "@echo off" > "$BATCH_PATH"
    echo "python \"$CREDIT_PATH\" %*" >> "$BATCH_PATH"
    
    echo "Batch file created at: $BATCH_PATH"
    echo "You may need to add this directory to your PATH manually."
else
    echo "Unsupported operating system. Please install manually."
    exit 1
fi

echo "Installation complete!"
echo "Run 'credit --setup' to configure your name and GitHub handle."