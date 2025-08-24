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
apt install -y python3 docker-ce docker-compose-plugin git maven


# Define variables and paths
PROJECT_DIR=$(pwd)
SERVICE_NAME="autofuzz"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
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

# Install and setup Vexgen
# Verify if docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Ensuring user is in docker group..."
usermod -aG docker ${SUDO_USER}
print_warning "Note: User may need to log out and back in for docker group changes to take effect."


## Before this step, it is necessary to create a vexgen's .env file by modifying the template.env file.
## The only changes needed are the values for the variables: GIT_GRAPHQL_API_KEY and NVD_API_KEY
if [ ! -d "vexgen" ]; then
    print_status "Installing Vexgen..."
    if ! git clone https://github.com/GermanMT/vexgen.git; then
        print_error "Failed to clone vexgen repository"
        exit 1
    fi
    rm -rf vexgen/.git
    rm -rf vexgen/.github
    print_success "Vexgen cloned successfully."
    cd vexgen
    # Setup .env file
    print_status "Setting up .env file..."
    cp template.env .env
    
    # Prompt for API keys
    echo "Please provide the following API keys (if a change of key is needed, modify vexgen/.env file):"
    read -p "Enter your GitHub GraphQL API key: " git_api_key
    read -p "Enter your NVD API key: " nvd_api_key
    
    # Update .env file with the provided API keys
    sed -i "s/GIT_GRAPHQL_API_KEY='add_your_api_key'/GITHUB_GRAPHQL_API_KEY='$git_api_key'/" .env
    sed -i "s/NVD_API_KEY='add_your_api_key'/NVD_API_KEY='$nvd_api_key'/" .env


    if [ -z "$git_api_key" ] || [ -z "$nvd_api_key" ]; then
        print_warning "API keys are empty. You can configure them later in vexgen/.env"
    fi
    
    print_success ".env file configured successfully."
    cd ..
else
    print_warning "Vexgen directory already exists, skipping clone."
fi
# Add pymongo dependency to requirements.txt
echo -e "\npymongo==4.7.0" >> vexgen/backend/requirements.txt 

# Setup OSS-Fuzz
if [ ! -d "OFF-Fuzz" ]; then
    print_status "Cloning OSS-Fuzz repository..."
    if ! git clone https://github.com/JosueRodLop/OSS-Fuzz.git; then
        print_error "Failed to clone OSS-Fuzz repository"
        exit 1
    fi
    rm -rf .git/
    rm -rf .github/
    rm -rf .gitattributes

# Create systemd service file
print_status "Creating systemd service file..."
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Autofuzz - Automated Fuzz Testing tool to detect vulnerable dependencies
Requires=docker.service
After=docker.service network.target
StartLimitIntervalSec=60
StartLimitBurst=4

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
Environment=COMPOSE_HTTP_TIMEOUT=120
Environment=DOCKER_CLIENT_TIMEOUT=120

ExecStart=docker compose -f ${PROJECT_DIR}/vexgen/docker-compose.yml up --build
ExecStop=docker compose -f ${PROJECT_DIR}/vexgen/docker-compose.yml down

# Configuración de usuario y permisos
User=${SUDO_USER:-root}
Group=docker

# Configuración de reinicio
Restart=on-failure
RestartSec=30

# Logs
StandardOutput=journal
StandardError=journal
SyslogIdentifier=autofuzz

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service file created at ${SERVICE_FILE}."


# Enable the service
print_status "Configuring systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME


# Create CLI script
print_status "Creating CLI script..."


tee /usr/local/bin/autofuzz > /dev/null <<EOF
#!/bin/bash

# Estas variables se rellenan con los valores de tu script de instalación
PYTHON_EXEC="${PYTHON_EXEC}"
MAIN_SCRIPT="${MAIN_SCRIPT}"

# La única línea de lógica:
# Ejecuta el script principal de Python y le pasa TODOS los argumentos ("\$@").
# La barra invertida asegura que "\$@" se escriba literalmente en el archivo.
"\$PYTHON_EXEC" "\$MAIN_SCRIPT" "\$@"
EOF

chmod +x /usr/local/bin/autofuzz

# Start the service
print_status "Starting Autofuzz service..."
sudo systemctl start $SERVICE_NAME

print_status "Waiting for the Vexgen service to be fully operational..."
max_attempts=300 # Esperar un máximo de 600 segundos (300 intentos * 2 segundos)
attempt=0
url_to_check="http://localhost:8000/docs" # Cambia el puerto si es diferente

while [ $attempt -lt $max_attempts ]; do
    # Usamos 'curl' para comprobar si el servicio responde.
    # El flag -s silencia la salida, -o /dev/null la descarta, y -I solo pide las cabeceras.
    # El código de estado de curl será 0 si tiene éxito.
    if curl -s -o /dev/null -I -w "%{http_code}" "$url_to_check" | grep -q "200"; then
        print_success "Vexgen service is up and running."
        break
    fi
    
    # Si no funciona, espera 2 segundos y vuelve a intentarlo
    echo -n "." # Imprime un punto para mostrar que está esperando
    sleep 2
    attempt=$((attempt + 1))
done
echo "" # Nueva línea después de los puntos

if [ $attempt -ge $max_attempts ]; then
    print_error "Timeout: The Vexgen service did not start in time."
    print_warning "You can check the service status with: systemctl status ${SERVICE_NAME}"
    print_warning "And the logs with: journalctl -xeu ${SERVICE_NAME}"
    print_warning "The service might just be taking longer to start. To check it manually, run the following command in another terminal:"
    print_warning "curl -I ${url_to_check}"
    exit 1
fi

print_status "Adjusting file ownership for the project directory..."
chown -R ${SUDO_USER}:${SUDO_GID:-$(id -g $SUDO_USER)} ${PROJECT_DIR}
print_success "File ownership adjusted."

print_success "Autofuzz service started successfully."
print_success "Installation and setup completed successfully."