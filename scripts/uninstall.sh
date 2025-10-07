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
CLI_FILE="/usr/local/bin/autofuzz"

print_status "Starting Autofuzz uninstallation..."

# Confirmation prompt
echo -e "${YELLOW}WARNING: This will completely remove Autofuzz and all its components.${NC}"
echo "The following actions will be performed:"
echo "  - Remove CLI command"
echo "  - Remove Python virtual environment"
echo "  - Remove java-analyzer build artifacts"
echo ""
echo "System packages (python3, python3-venv, git, maven, openjdk-17-jdk, curl) will NOT be removed."
echo ""
read -p "Are you sure you want to continue? (y/N): " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_warning "Uninstallation cancelled by user."
    exit 0
fi

# Remove CLI command
if [ -f "$CLI_FILE" ]; then
    print_status "Removing CLI command..."
    rm -f $CLI_FILE
    print_success "CLI command removed."
else
    print_warning "CLI command file not found."
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
if [ ! -f "$CLI_FILE" ] && [ ! -d "venv" ] && [ ! -d "java-analyzer/target" ]; then
    print_success "All main components successfully removed."
else
    print_warning "Some components may still exist. Please check manually:"
    [ -f "$CLI_FILE" ] && echo "  - CLI file: $CLI_FILE"
    [ -d "venv" ] && echo "  - Python virtual environment"
    [ -d "java-analyzer/target" ] && echo "  - Java-analyzer build artifacts"
fi

print_status "System packages (python3, python3-venv, git, maven, openjdk-17-jdk, curl) were preserved."
print_warning "Remember to remove any remaining project files manually if needed."