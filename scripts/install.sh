#!/bin/bash
# This script installs and setups the necessary environment for the project.

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


# Install necessary packages
print_status "Installing necessary packages..."
apt update
apt install -y python3 python3-venv git maven openjdk-17-jdk curl


# Define variables and paths
PROJECT_DIR=$(pwd)
PYTHON_EXEC="${PROJECT_DIR}/venv/bin/python"
MAIN_SCRIPT="${PROJECT_DIR}/src/main.py"

# Set Virtual Environment
print_status "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists, skipping creation"
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
$PYTHON_EXEC -m pip install --upgrade pip
$PYTHON_EXEC -m pip install -r requirements.txt
print_success "Python dependencies installed successfully."


# Generate java-analyzer package
print_status "Generating java-analyzer package..."
cd java-analyzer
mvn clean package -DskipTests
cd ..

# Validate Java installation
print_status "Validating Java installation..."
if ! command -v java &> /dev/null; then
    print_error "Java not found. Please ensure Java 17+ is installed."
    exit 1
fi

java_version=$(java -version 2>&1 | grep -o '".*"' | sed 's/"//g')
print_success "Java found: $java_version" 

# Setup OSS-Fuzz
if [ ! -d "OSS-Fuzz" ]; then
    print_status "Cloning OSS-Fuzz repository..."
    if ! git clone https://github.com/JosueRodLop/OSS-Fuzz.git; then
        print_error "Failed to clone OSS-Fuzz repository"
        exit 1
    fi
    print_success "OSS-Fuzz cloned successfully."
else
    print_warning "OSS-Fuzz directory already exists, skipping clone."
fi

# Validate installation components
print_status "Validating installation..."
if [ ! -f "$PYTHON_EXEC" ]; then
    print_error "Python virtual environment not found at $PYTHON_EXEC"
    exit 1
fi

if [ ! -f "$MAIN_SCRIPT" ]; then
    print_error "Main script not found at $MAIN_SCRIPT"
    exit 1
fi

if [ ! -f "java-analyzer/target/java-analyzer-1.0-SNAPSHOT-jar-with-dependencies.jar" ]; then
    print_error "Java analyzer JAR not found. Build might have failed."
    exit 1
fi

print_success "All components validated successfully."

# Create CLI script
print_status "Creating CLI script..."

tee /usr/local/bin/autofuzz > /dev/null <<EOF
#!/bin/bash

# TestGenerator CLI wrapper
PYTHON_EXEC="${PYTHON_EXEC}"
MAIN_SCRIPT="${MAIN_SCRIPT}"

# Execute the main Python script with all provided arguments
"\$PYTHON_EXEC" "\$MAIN_SCRIPT" "\$@"
EOF

chmod +x /usr/local/bin/autofuzz
print_success "CLI script created successfully."

# Test CLI installation
print_status "Testing CLI installation..."
if command -v autofuzz &> /dev/null; then
    print_success "CLI command 'autofuzz' is available system-wide."
else
    print_error "CLI installation failed."
    exit 1
fi

print_status "Adjusting file ownership for the project directory..."
chown -R ${SUDO_USER}:${SUDO_GID:-$(id -g $SUDO_USER)} ${PROJECT_DIR}
print_success "File ownership adjusted."

print_success "TestGenerator installation completed successfully!"
echo ""
echo "======================================"
echo "🎉 Installation Summary:"
echo "======================================"
echo "✓ Python virtual environment created"
echo "✓ Python dependencies installed" 
echo "✓ Java analyzer built successfully"
echo "✓ OSS-Fuzz repository cloned"
echo "✓ CLI tool 'autofuzz' installed"
echo ""
echo "Usage:"
echo "  autofuzz --help               # Show help"
echo "  autofuzz <project_path>       # Analyze a project"
echo ""
echo "Project directory: ${PROJECT_DIR}"
echo "======================================"