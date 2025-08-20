#!/bin/bash
# This script uninstalls and removes the Autofuzz project environment.

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Access denied. Please, run this script with sudo." >&2
  exit 1
fi

# Output colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Pretty print function
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

# Define variables and paths
PROJECT_DIR=$(pwd)
SERVICE_NAME="autofuzz"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
CLI_FILE="/usr/local/bin/autofuzz"

print_status "Starting Autofuzz uninstallation..."

# Confirmation prompt
echo -e "${YELLOW}WARNING: This will completely remove Autofuzz and all its components.${NC}"
echo "The following actions will be performed:"
echo "  - Stop and disable the Autofuzz service"
echo "  - Remove systemd service file"
echo "  - Remove CLI command"
echo "  - Remove vexgen directory and containers"
echo "  - Remove Python virtual environment"
echo "  - Remove java-analyzer build artifacts"
echo ""
echo "System packages (python3, docker-ce, git, maven) will NOT be removed."
echo ""
read -p "Are you sure you want to continue? (y/N): " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_warning "Uninstallation cancelled by user."
    exit 0
fi

# Stop and disable the service
if systemctl is-active --quiet $SERVICE_NAME; then
    print_status "Stopping Autofuzz service..."
    systemctl stop $SERVICE_NAME
    print_success "Autofuzz service stopped."
else
    print_warning "Autofuzz service was not running."
fi

if systemctl is-enabled --quiet $SERVICE_NAME; then
    print_status "Disabling Autofuzz service..."
    systemctl disable $SERVICE_NAME
    print_success "Autofuzz service disabled."
else
    print_warning "Autofuzz service was not enabled."
fi

# Remove systemd service file
if [ -f "$SERVICE_FILE" ]; then
    print_status "Removing systemd service file..."
    rm -f $SERVICE_FILE
    systemctl daemon-reload
    print_success "Systemd service file removed."
else
    print_warning "Systemd service file not found."
fi

# Remove CLI command
if [ -f "$CLI_FILE" ]; then
    print_status "Removing CLI command..."
    rm -f $CLI_FILE
    print_success "CLI command removed."
else
    print_warning "CLI command file not found."
fi

# Stop and remove vexgen Docker containers and images
if [ -d "vexgen" ]; then
    print_status "Stopping and removing vexgen Docker containers..."
    cd vexgen
    
    # Stop containers if running
    if docker compose ps -q &> /dev/null; then
        docker compose down --volumes --remove-orphans 2>/dev/null || true
        print_success "Vexgen containers stopped and removed."
    else
        print_warning "No vexgen containers found running."
    fi
    
    # Remove Docker images related to vexgen
    print_status "Removing vexgen Docker images..."
    docker images --format "table {{.Repository}}:{{.Tag}}" | grep "vexgen" | xargs -r docker rmi 2>/dev/null || true
    
    cd ..
    
    # Remove vexgen directory
    print_status "Removing vexgen directory..."
    rm -rf vexgen
    print_success "Vexgen directory removed."
else
    print_warning "Vexgen directory not found."
fi

# Remove Python virtual environment
if [ -d "venv" ]; then
    print_status "Removing Python virtual environment..."
    rm -rf venv
    print_success "Python virtual environment removed."
else
    print_warning "Python virtual environment not found."
fi

# Remove java-analyzer build artifacts
if [ -d "java-analyzer/target" ]; then
    print_status "Removing java-analyzer build artifacts..."
    rm -rf java-analyzer/target
    print_success "Java-analyzer build artifacts removed."
else
    print_warning "Java-analyzer build artifacts not found."
fi

# Clean up Docker system (optional)
print_status "Cleaning up Docker system..."
read -p "Do you want to clean up unused Docker resources (images, containers, networks)? (y/N): " cleanup_docker

if [[ $cleanup_docker =~ ^[Yy]$ ]]; then
    docker system prune -f 2>/dev/null || true
    print_success "Docker system cleaned up."
else
    print_warning "Docker system cleanup skipped."
fi

print_success "Autofuzz uninstallation completed successfully."

# Final status check
print_status "Final status check:"
if [ ! -f "$SERVICE_FILE" ] && [ ! -f "$CLI_FILE" ] && [ ! -d "vexgen" ] && [ ! -d "venv" ]; then
    print_success "All main components successfully removed."
else
    print_warning "Some components may still exist. Please check manually:"
    [ -f "$SERVICE_FILE" ] && echo "  - Service file: $SERVICE_FILE"
    [ -f "$CLI_FILE" ] && echo "  - CLI file: $CLI_FILE"
    [ -d "vexgen" ] && echo "  - Vexgen directory"
    [ -d "venv" ] && echo "  - Python virtual environment"
fi

print_status "System packages (python3, docker-ce, docker-compose-plugin, git, maven) were preserved."
print_warning "Remember to remove any remaining project files manually if needed."