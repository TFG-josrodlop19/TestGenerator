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
else
    echo "Vexgen directory already exists, skipping clone."
fi
echo "pymongo==4.7.0" >> vexgen/backend/requirements.txt 
cd vexgen/
# docker compose up -d --build

