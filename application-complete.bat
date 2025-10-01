@echo off
chcp 65001 >nul
title  EcoMarché Dashboard - Application Complète
echo ========================================
echo     ECO-MARCHE DASHBOARD - FULL STACK
echo ========================================
echo.

setlocal EnableDelayedExpansion

:: Vérifications
if not exist "backend" (
    echo  Dossier backend manquant
    pause
    exit /b 1
)

if not exist "ecomarche-frontend" (
    echo   Frontend non trouvé - mode API seul
    set FRONTEND_MODE=api
) else (
    set FRONTEND_MODE=full
)

cd backend

echo [1/6]  Verification Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python requis - installez-le depuis python.org
    pause
    exit /b 1
)

echo [2/6]   Environnement...
if not exist "venv" (
    echo  Creation venv...
    python -m venv venv
)

echo [3/6]  Dependances...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1

echo [4/6]  Preparation frontend...
if "!FRONTEND_MODE!"=="full" (
    if not exist "..\ecomarche-frontend\dist" (
        echo   Frontend non compile - mode API
        set FRONTEND_MODE=api
    ) else (
        echo  Frontend detecte
    )
)

echo [5/6]  Ouverture navigateur...
echo Ouverture de l'application...
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8000"

echo [6/6]  Demarrage...
echo.
echo ========================================
echo     ECO-MARCHE DASHBOARD - ACTIF
echo ========================================
echo.
if "!FRONTEND_MODE!"=="full" (
    echo  MODE COMPLET : Interface web + API
) else (
    echo  MODE API : Backend seul
)
echo.
echo  URL : http://127.0.0.1:8000
echo  API : http://127.0.0.1:8000/api/produits/all
echo.
echo  Testez les endpoints directement dans le navigateur
echo   Ctrl+C pour arreter
echo ========================================
echo.

python app.py

echo.
echo Fermeture de l'application...
timeout /t 2 >nul