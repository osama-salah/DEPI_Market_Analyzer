#!/bin/bash

cd web_server/

# Install the requirements
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install plotly

# Run the servers
nohup python web_server.py &
nohup .venv/bin/streamlit run streamlit/home.py &
