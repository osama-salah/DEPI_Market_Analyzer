@echo off
REM Manual start script for ML Server and Price Predictor

REM Start ML Server
echo Starting ML Server...
cd ML_server
call .venv\Scripts\activate
start /b python ml_server.py
call deactivate
cd ..

REM Start Price Predictor
echo Starting Price Predictor...
cd price_predictor
call .venv\Scripts\activate
start /b python price_predictor.py
call deactivate
cd ..

echo ML servers have been started!
