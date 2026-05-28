@echo off
:MENU
cls
color 0B
echo ========================================================
echo          🛡️  SCAMGUARD SHIELD LAUNCHER CONSOLE  🛡️
echo ========================================================
echo.
echo Please select an option:
echo.
echo [1] Run Full Application (Backend + Frontend + Chrome Guest)
echo [2] Run Frontend Only (React Vite + Chrome Guest)
echo [3] Run Backend Only (FastAPI Server)
echo [4] Download and Setup Datasets
echo [5] Train Machine Learning Models
echo [6] Test and Compare Models (Evaluation)
echo [7] Run Hyperparameter Tuning (Optuna)
echo [8] Run Exploratory Data Analysis (EDA)
echo [9] Exit
echo.
echo ========================================================
set /p choice="Enter your selection (1-9): "

if "%choice%"=="1" goto FULL_APP
if "%choice%"=="2" goto FRONTEND_ONLY
if "%choice%"=="3" goto BACKEND_ONLY
if "%choice%"=="4" goto SETUP_DATA
if "%choice%"=="5" goto TRAIN_MODELS
if "%choice%"=="6" goto COMPARE_MODELS
if "%choice%"=="7" goto HYPER_TUNE
if "%choice%"=="8" goto RUN_EDA
if "%choice%"=="9" goto EXIT
goto INVALID

:FULL_APP
cls
echo ========================================================
echo          🚀 LAUNCHING FULL APPLICATION 🚀
echo ========================================================
echo [1/3] Launching FastAPI ML Backend Server...
start "ScamGuard Backend" cmd /k "cd /d "%~dp0" && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
echo.
echo [2/3] Launching React Vite Frontend Console...
start "ScamGuard Frontend" cmd /k "cd /d "%~dp0\frontend" && node node_modules\vite\bin\vite.js"
echo.
echo Waiting 3 seconds for local servers to boot...
timeout /t 3 /nobreak >nul
echo.
echo [3/3] Launching Google Chrome in Guest Mode...
start chrome --guest "http://localhost:5173"
echo.
echo System fully launched.
pause
goto MENU

:FRONTEND_ONLY
cls
echo ========================================================
echo          🎨 LAUNCHING FRONTEND DASHBOARD ONLY 🎨
echo ========================================================
echo [1/2] Launching React Vite Frontend Console...
start "ScamGuard Frontend" cmd /k "cd /d "%~dp0\frontend" && node node_modules\vite\bin\vite.js"
echo.
echo Waiting 2 seconds...
timeout /t 2 /nobreak >nul
echo.
echo [2/2] Launching Google Chrome in Guest Mode...
start chrome --guest "http://localhost:5173"
echo.
echo Frontend launched.
pause
goto MENU

:BACKEND_ONLY
cls
echo ========================================================
echo          🛰️  LAUNCHING FASTAPI BACKEND SERVER ONLY  🛰️
echo ========================================================
echo Launching FastAPI ML Backend Server...
start "ScamGuard Backend" cmd /k "cd /d "%~dp0" && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
echo.
echo Backend launched.
pause
goto MENU

:SETUP_DATA
cls
echo ========================================================
echo          📥 DOWNLOADING AND SETTING UP DATASETS 📥
echo ========================================================
cd /d "%~dp0"
python ml_pipeline\download_and_setup_datasets.py
echo.
echo Dataset setup completed.
pause
goto MENU

:TRAIN_MODELS
cls
echo ========================================================
echo          🏋️‍♂️ TRAINING MACHINE LEARNING MODELS 🏋️‍♂️
echo ========================================================
cd /d "%~dp0"
python ml_pipeline\train_models.py
echo.
echo Model training completed.
pause
goto MENU

:COMPARE_MODELS
cls
echo ========================================================
echo          📊 TESTING & COMPARING MODELS (EVALUATION) 📊
echo ========================================================
cd /d "%~dp0"
python ml_pipeline\compare_models.py
echo.
echo Model evaluation and comparison completed.
pause
goto MENU

:HYPER_TUNE
cls
echo ========================================================
echo          ⚡ OPTUNA HYPERPARAMETER TUNING ⚡
echo ========================================================
cd /d "%~dp0"
python ml_pipeline\tune_hyperparameters.py
echo.
echo Hyperparameter tuning completed.
pause
goto MENU

:RUN_EDA
cls
echo ========================================================
echo          📈 EXPLORATORY DATA ANALYSIS (EDA) 📈
echo ========================================================
cd /d "%~dp0"
python ml_pipeline\eda.py
echo.
echo Exploratory Data Analysis completed. Visualizations saved.
pause
goto MENU

:INVALID
echo.
echo Invalid selection. Please choose a number between 1 and 9.
timeout /t 2 >nul
goto MENU

:EXIT
echo.
echo Goodbye!
exit
