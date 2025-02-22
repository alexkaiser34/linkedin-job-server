#!/bin/bash

# Add timestamp to log
echo "====================================="
date
echo "Starting scraper..."

# Navigate to the project directory
cd /home/ubuntu/LinkedIn-Job-Scraper

# Run the Python script
python3 main.py

# Log completion
echo "Scraper finished at: "
date
echo "====================================="