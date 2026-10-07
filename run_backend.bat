@echo off
echo ===================================================
echo   Industrial Predictive Maintenance - Backend API
echo ===================================================
cd /d "%~dp0"

echo [1/3] Checking Python dependencies...
pip install -r requirements.txt

echo [2/3] Checking Machine Learning Model...
if not exist "models\rf_rul_model.pkl" (
    echo Model not found. Training Random Forest model now...
    python model/train_model.py
) else (
    echo Trained model found in models/ directory.
)

echo [3/3] Starting FastAPI server on http://127.0.0.1:8000 ...
python main.py
pause
