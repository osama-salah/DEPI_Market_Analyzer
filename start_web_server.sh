#!/bin/bash

# Manual start script for ML Server, Price Predictor, and Web Server

# Navigate to Web Server and activate the virtual environment
echo "Starting Web Server..."
cd ./web_server/
source .venv/bin/activate
nohup python web_server.py &
nohup .venv/bin/streamlit run streamlit/home.py &
deactivate
cd ..

echo "Web Server has been started!"
