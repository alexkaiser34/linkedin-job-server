#!/bin/bash

# Install the models package in development mode
cd models
pip3 install -e .
cd ..

# Create symlinks for local development (optional)
ln -s $(pwd)/models/job_assistant_models api/job_assistant_models
ln -s $(pwd)/models/job_assistant_models aws/job_assistant_models
ln -s $(pwd)/models/job_assistant_models scraper/job_assistant_models

echo "Development environment set up successfully!" 