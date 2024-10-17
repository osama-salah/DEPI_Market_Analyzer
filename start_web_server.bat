@echo off
REM Manual start script for Web Server

REM Start Web Server
echo Starting Web Server...
cd web_server
call .venv\Scripts\activate
start /b python web_server.py
start /b .venv\Scripts\streamlit run streamlit\home.py
call deactivate
cd ..

echo Web Server has been started!

