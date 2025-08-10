#!/bin/bash

# This script installs and setups the necessary environment for the project.

# Install and setup Vexgen

## Before this step, it is necessary to create a vexgen's .env file by modifying the template.env file.
## The only changes needed are the values for the variables: GIT_GRAPHQL_API_KEY and NVD_API_KEY
if [ ! -d "vexgen" ]; then
    echo "Installing Vexgen..."
    git clone git@github.com:GermanMT/vexgen.git
    rm -rf vexgen/.git
    rm -rf vexgen/.github
    echo "Vexgen cloned successfully."
    cd vexgen
    # Setup .env file
    echo "Setting up .env file..."
    cp template.env .env
    
    # Prompt for API keys
    echo "Please provide the following API keys (if a change of key is needed, modify vexgen/.env file):"
    read -p "Enter your GitHub GraphQL API key: " git_api_key
    read -p "Enter your NVD API key: " nvd_api_key
    
    # Update .env file with the provided API keys
    sed -i "s/GIT_GRAPHQL_API_KEY='add_your_api_key'/GITHUB_GRAPHQL_API_KEY='$git_api_key'/" .env
    sed -i "s/NVD_API_KEY='add_your_api_key'/NVD_API_KEY='$nvd_api_key'/" .env
    
    echo ".env file configured successfully."
    cd ..
else
    echo "Vexgen directory already exists, skipping clone."
fi
# Add pymongo dependency to requirements.txt
echo -e "\npymongo==4.7.0" >> vexgen/backend/requirements.txt 
cd vexgen
docker compose up -d --build
cd ..
