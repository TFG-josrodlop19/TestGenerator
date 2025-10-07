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
echo "  - Remove OSS-Fuzz repository"
echo ""
echo "System packages (python3, python3-venv, git, maven, openjdk-17-jdk, curl, docker) will NOT be removed."
echo ""
read -p "Are you sure you want to continue? (y/N): " confirm

if [[ ! $confirm =~ ^[Yy]([Ee][Ss])?$ ]]; then
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

# Remove Python cache files
print_status "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
print_success "Python cache files removed."

# Remove OSS-Fuzz repository
if [ -d "OSS-Fuzz" ]; then
    print_status "Removing OSS-Fuzz repository..."
    rm -rf OSS-Fuzz
    print_success "OSS-Fuzz repository removed."
else
    print_warning "OSS-Fuzz repository not found."
fi

# Optional: Clean Docker containers and images related to the project
print_status "Docker cleanup..."
read -p "Do you want to clean up TestGenerator-related Docker resources? (y/N): " cleanup_docker

if [[ $cleanup_docker =~ ^[Yy]$ ]]; then
    print_status "Cleaning up Docker images and containers..."
    # Remove any containers related to tfg-josrodlop19 projects
    docker ps -a --filter "name=tfg-josrodlop19" -q | xargs -r docker rm -f 2>/dev/null || true
    # Remove any images related to the project
    docker images --filter "reference=gcr.io/oss-fuzz/tfg-josrodlop19*" -q | xargs -r docker rmi -f 2>/dev/null || true
    print_success "Docker cleanup completed."
else
    print_warning "Docker cleanup skipped."
fi

print_success "TestGenerator uninstallation completed successfully."

# Final status check
print_status "Final status check:"
if [ ! -f "$CLI_FILE" ] && [ ! -d "venv" ] && [ ! -d "java-analyzer/target" ] && [ ! -d "OSS-Fuzz" ]; then
    print_success "All main components successfully removed."
else
    print_warning "Some components may still exist. Please check manually:"
    [ -f "$CLI_FILE" ] && echo "  - CLI file: $CLI_FILE"
    [ -d "venv" ] && echo "  - Python virtual environment"
    [ -d "java-analyzer/target" ] && echo "  - Java-analyzer build artifacts"
    [ -d "OSS-Fuzz" ] && echo "  - OSS-Fuzz repository"
fi

print_status "System packages (python3, python3-venv, git, maven, openjdk-17-jdk, curl, docker) were preserved."
print_warning "Remember to remove any remaining project files manually if needed."