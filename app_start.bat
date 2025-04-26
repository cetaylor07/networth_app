@echo off
start cmd /k "cd /d C:\NetworthApp && call env\Scripts\activate && uvicorn main:app --reload"
timeout /t 5
start cmd /k "cd /d C:\NetworthApp && call env\Scripts\activate && streamlit run app.py"
