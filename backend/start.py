"""
Script de démarrage pour l'application EcoMarché
"""
import os
from app import app

if __name__ == "__main__":
    # Créer le dossier pour les modèles sauvegardés s'il n'existe pas
    os.makedirs("./model/saved_models", exist_ok=True)
    
    # Lancer l'application
    app.run(debug=True, host="0.0.0.0", port=8000)