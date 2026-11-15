#!/bin/bash

echo "Starting SWRO Frontend deployment..."

# Check if .next directory exists
if [ ! -d ".next" ]; then
    echo ".next directory not found. Building the application..."
    npm run build
    if [ $? -ne 0 ]; then
        echo "Build failed. Exiting..."
        exit 1
    fi
    echo "Build completed successfully."
else
    echo ".next directory found. Skipping build."
fi

# Start the server
echo "Starting the server..."
node server.js
