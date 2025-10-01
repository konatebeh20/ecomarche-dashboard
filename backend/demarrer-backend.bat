@echo off
chcp 65001 >nul
title  EcoMarché Dashboard - Application Complète
echo ========================================
echo     ECO-MARCHE DASHBOARD - COMPLET
echo ========================================
echo.

:: Vérifier le dossier
if not exist "backend" (
    echo  Erreur : Dossier 'backend' non trouvé
    pause
    exit /b 1
)

cd backend

echo [1/5]  Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python non installe - voir instructions dans README.md
    pause
    exit /b 1
)

echo [2/5]   Environnement virtuel...
if not exist "venv" (
    echo  Creation venv...
    python -m venv venv
)

echo [3/5]  Installation dependances...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1

echo [4/5]  Ouverture navigateur...
echo Ouverture de l'application dans le navigateur...
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000"

echo [5/5]  Demarrage application...
echo.
echo ========================================
echo     ECO-MARCHE DASHBOARD - PRET
echo ========================================
echo.
echo  Application accessible sur :
echo  http://127.0.0.1:8000
echo.
echo  Interface web complete
echo  Données en temps reel
echo  Recommendations actives
echo.
echo   Ctrl+C pour arreter
echo ========================================
echo.

python app.py

echo.
echo Application arretee. Fermeture...
timeout /t 3 >nul