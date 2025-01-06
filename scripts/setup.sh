#!/bin/bash
set -e

# Create necessary directories
mkdir -p data
mkdir -p logs

# Set permissions
chmod 777 data
chmod 777 logs

echo "Directory setup complete" 