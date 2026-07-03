@echo off
echo ==========================================
echo Advanced SentiWise Analysis Pipeline
echo ==========================================

echo [1] Checking Data...
if not exist "data\reviews_dataset.csv" (
    echo Generating sample data...
    python data\generate_sample_data.py
) else (
    echo Data found.
)

echo.
echo [2] Starting Backend API...
echo The dashboard will be available at: http://127.0.0.1:8000/app/index.html
echo.

uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
