#!/bin/bash

# Activate the virtual environment
source env/bin/activate

# Start the FastAPI backend
uvicorn main:app --reload &

# Wait a second
sleep 2

# Start the Streamlit app
streamlit run your_streamlit_app.py
