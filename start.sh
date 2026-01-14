#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="/etc/systemd/system/serveralert.service"
COMMAND="${1:-run}"

install_service() {
    echo "Installing ServerAlert systemd service..."
    if [ ! -f "$SCRIPT_DIR/serveralert.service" ]; then
        echo "Missing service template: $SCRIPT_DIR/serveralert.service"
        exit 1
    fi

    cp "$SCRIPT_DIR/serveralert.service" "$SERVICE_FILE"
    systemctl daemon-reload
    systemctl enable serveralert
    echo "Service installed and enabled."
}

uninstall_service() {
    echo "Uninstalling ServerAlert systemd service..."
    systemctl stop serveralert || true
    systemctl disable serveralert || true
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
    echo "Service removed."
}

run_service() {
    cd "$SCRIPT_DIR"

    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 is not installed."
        exit 1
    fi

    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv

        if [ $? -ne 0 ]; then
            echo "Failed to create virtual environment. Install python3-venv first."
            exit 1
        fi

        source venv/bin/activate
        pip install --upgrade pip
        echo "Installing dependencies..."
        pip install psutil requests
    else
        source venv/bin/activate
    fi

    echo "Starting ServerAlert..."
    python3 serveralert.py
}

case "$COMMAND" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    run|start)
        run_service
        ;;
    *)
        echo "Usage: $0 [run|install|uninstall]"
        exit 1
        ;;
esac
