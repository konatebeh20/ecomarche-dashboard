import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta
import os

class DemandPredictionModel:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        self.model_path = os.path.join(os.path.dirname(__file__), "prediction_model.joblib")
        
        # Charger le modèle s'il existe
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print("Modèle de prédiction chargé avec succès")
            except Exception as e:
                print(f"Erreur lors du chargement du modèle: {e}")
                self.train_mock_model()
        else:
            print("Aucun modèle trouvé, création d'un modèle simulé")
            self.train_mock_model()
    
    def train_mock_model(self):
        """Entraîne un modèle simulé avec des données fictives"""
        # Créer des données d'entraînement fictives
        np.random.seed(42)
        
        # Caractéristiques: jour de la semaine (0-6), mois (1-12), catégorie (0-4), prix (5-20)
        X_train = np.random.rand(100, 4)
        X_train[:, 0] = np.random.randint(0, 7, 100)  # jour de la semaine
        X_train[:, 1] = np.random.randint(1, 13, 100)  # mois
        X_train[:, 2] = np.random.randint(0, 5, 100)  # catégorie
        X_train[:, 3] = np.random.uniform(5, 20, 100)  # prix
        
        # Cible: demande journalière (entre 10 et 100)
        base_demand = 30
        y_train = base_demand + 10 * X_train[:, 0] + 5 * X_train[:, 1] + np.random.normal(0, 5, 100)
        
        # Entraîner le modèle
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Sauvegarder le modèle
        joblib.dump(self.model, self.model_path)
        print("Modèle simulé entraîné et sauvegardé")
    
    def predict(self, product_id, days=7, category_id=0, price=10.0):
        """
        Prédit la demande pour un produit sur plusieurs jours
        
        Args:
            product_id: Identifiant du produit
            days: Nombre de jours pour la prédiction
            category_id: ID de la catégorie du produit
            price: Prix du produit
            
        Returns:
            Liste de prédictions quotidiennes
        """
        if not self.is_trained:
            self.train_mock_model()
        
        predictions = []
        today = datetime.now()
        
        for day in range(1, days + 1):
            date = today + timedelta(days=day)
            
            # Caractéristiques pour la prédiction
            features = np.array([
                date.weekday(),  # jour de la semaine (0-6)
                date.month,      # mois (1-12)
                category_id,     # catégorie
                price            # prix
            ]).reshape(1, -1)
            
            # Prédiction
            prediction = max(5, int(self.model.predict(features)[0]))
            
            # Ajouter un peu de variation aléatoire pour simuler des fluctuations réalistes
            variation = np.random.normal(0, prediction * 0.1)
            prediction = max(1, int(prediction + variation))
            
            predictions.append({
                "date": date.strftime("%Y-%m-%d"),
                "prediction": prediction
            })
        
        return predictions

# Créer une instance du modèle pour l'utiliser dans l'API
demand_model = DemandPredictionModel()