"""
Constantes pour l'application EcoMarché
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# ============================
# CONFIGURATION DE L'APPLICATION
# ============================

APP_NAME = "EcoMarché API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "API pour l'application de réduction du gaspillage alimentaire EcoMarché"

# ============================
# CONFIGURATION DE LA BASE DE DONNÉES
# ============================

# Valeur par défaut (SQLite)
DATABASE_URL = "sqlite:///./ecomarche.db"

# Si une variable d'environnement DATABASE_URL existe, elle prend la priorité
if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")

# ============================
# CONFIGURATION DES MODÈLES ML
# ============================

MODEL_DIR = "./model/saved_models"
PREDICTION_MODEL_PATH = f"{MODEL_DIR}/prediction_model.pkl"
PRICING_MODEL_PATH = f"{MODEL_DIR}/pricing_model.pkl"

# ============================
# PARAMÈTRES DES MODÈLES
# ============================

DEFAULT_PREDICTION_DAYS = 7
MAX_PREDICTION_DAYS = 30
MIN_STOCK_THRESHOLD = 5
MAX_REDUCTION_PERCENTAGE = 90

# ============================
# CATÉGORIES DE PRODUITS
# ============================

CATEGORIES = {
    1: "Produits laitiers",
    2: "Boulangerie",
    3: "Fruits",
    4: "Légumes",
    5: "Viandes",
    6: "Poissons",
    7: "Épicerie",
    8: "Boissons",
    9: "Surgelés",
    10: "Hygiène"
}

# ============================
# STATUTS DES PRODUITS
# ============================

STATUT_EN_STOCK = "En stock"
STATUT_STOCK_BAS = "Stock bas"
STATUT_RUPTURE = "Rupture de stock"
STATUT_COMMANDE = "Commandé"

# ============================
# SEUILS POUR LES ALERTES
# ============================

SEUIL_PEREMPTION_CRITIQUE = 3  # jours
SEUIL_PEREMPTION_ATTENTION = 7  # jours
SEUIL_PEREMPTION_NORMAL = 14  # jours

# ============================
# CONFIGURATION CORS
# ============================

CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:4200",
    "http://localhost:80",
    "http://frontend"
]

# ============================
# CONFIGURATION LOGGING
# ============================

LOG_LEVEL = "INFO"
LOG_FILE = "./log/ecomarche.log"

# ============================
# CONFIGURATION POSTGRESQL
# ============================

# Exemple de connexion PostgreSQL par défaut
POSTGRESQL_URL = "postgresql+psycopg2://postgres:MotDePasse@localhost:5432/ecomarche_db"

# Priorité : variable d'environnement DATABASE_URL
if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    DATABASE_URL = POSTGRESQL_URL  # Par défaut PostgreSQL
