#!/bin/bash

# Manual start script for ML Server and Price Predictor

# Navigate to ML Server and activate the virtual environment
echo "Starting ML Server..."
cd ./ML_server/
source .venv/bin/activate
GENAI_API_KEY="AIzaSyCJI7IE3ZaoxajrjGbwxvylEEpviAOw1kU" nohup python ml_server.py &
deactivate
cd ..

# Navigate to Price Predictor and activate the virtual environment
echo "Starting Price Predictor..."
cd ./price_predictor/
source .venv/bin/activate
nohup python price_predictor.py &
deactivate

echo "ML Servers have been started!"
