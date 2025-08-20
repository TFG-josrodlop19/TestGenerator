#!/bin/bash
# This script uninstalls the project, cleaning up services, Docker containers, and files.

set -e # Exit immediately if a command exits with a non-zero status.

# Verify the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Error: Access denied. Please, run this script with sudo." >&2
  exit 1
fi

# --- Output colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Pretty print functions ---
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# --- Define variables and paths ---
# This assumes you are running the script from the project's root directory
PROJECT_DIR=$(pwd)
SERVICE_NAME="autofuzz"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

print_status "Starting the uninstallation process for Autofuzz..."
echo "-----------------------------------------------------"

# --- 1. Stop and disable the systemd service ---
print_status "Stopping and disabling the systemd service..."
if systemctl is-active --quiet $SERVICE_NAME; then
    systemctl stop $SERVICE_NAME
    print_success "Service stopped."
else
    print_warning "Service was not running."
fi

if systemctl is-enabled --quiet $SERVICE_NAME; then
    systemctl disable $SERVICE_NAME
    print_success "Service disabled."
else
    print_warning "Service was not enabled."
fi

# --- 2. Remove CLI script and systemd service file ---
print_status "Removing CLI script and service file..."
if [ -f "/usr/local/bin/autofuzz" ]; then
    rm -f /usr/local/bin/autofuzz
    print_success "CLI script /usr/local/bin/autofuzz removed."
else
    print_warning "CLI script not found, skipping."
fi

if [ -f "$SERVICE_FILE" ]; then
    rm -f "$SERVICE_FILE"
    print_success "Systemd service file ${SERVICE_FILE} removed."
else
    print_warning "Service file not found, skipping."
fi

# Reload systemd to apply changes
systemctl daemon-reload
print_success "Systemd daemon reloaded."

# --- 3. Clean and remove Vexgen Docker environment ---
print_status "Cleaning up Vexgen Docker environment..."
if [ -d "vexgen" ]; then
    cd vexgen
    print_status "Bringing down Docker Compose containers and volumes..."
    # The '--rmi all' flag removes all images used by the services.
    # The '-v' flag removes named volumes.
    docker compose down --rmi all -v
    cd ..
    
    print_status "Removing Vexgen directory..."
    rm -rf vexgen
    print_success "Vexgen cleanup complete."
else
    print_warning "Vexgen directory not found, skipping cleanup."
fi

# --- 4. Clean Python environment ---
print_status "Removing Python environment..."
if [ -d "venv" ]; then
    rm -rf venv
    print_success "Virtual environment 'venv' removed."
else
    print_warning "Virtual environment not found, skipping."
fi

# --- 5. Information about system packages ---
print_warning "This script will NOT uninstall system-level packages like python3, docker, git, or maven."
print_warning "These are shared dependencies and should be removed manually if you are sure no other application needs them."
print_warning "Example command: sudo apt purge python3 docker docker-compose git maven"


echo "-----------------------------------------------------"
print_success "Uninstallation completed successfully."