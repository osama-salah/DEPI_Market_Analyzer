#!/bin/bash

cd ML_server/

# Install ML Server requirements
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip &&
pip install torch==2.4.1 --extra-index-url https://download.pytorch.org/whl/cpu &&
pip install -r requirements.txt &&
pip install -U google-generativeai &&

# Run the ML server
GENAI_API_KEY="AIzaSyCJI7IE3ZaoxajrjGbwxvylEEpviAOw1kU" nohup python ml_server.py &
deactivate

cd ../price_predictor
# Install Price Predictor requirements
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run Price Predictor server
nohup python price_predictor.py &
deactivate
