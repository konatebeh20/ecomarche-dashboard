# Instructions de Test - EcoMarché Dashboard

## Backend (API Flask) - TESTABLE SANS FRONTEND

### 1. Démarrer le backend :
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py




### 2. Tester l'API directement dans le navigateur :
Liste des produits : http://127.0.0.1:8000/api/produits/all

KPIs : http://127.0.0.1:8000/api/kpi/overview

Recommandations : http://127.0.0.1:8000/api/kpi/waste_recommendations