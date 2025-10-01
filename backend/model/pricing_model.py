import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingRegressor
from datetime import datetime, timedelta
import os

class DynamicPricingModel:
    def __init__(self):
        self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        self.model_path = os.path.join(os.path.dirname(__file__), "pricing_model.joblib")
        
        # Charger le modèle s'il existe
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print("Modèle de tarification chargé avec succès")
            except Exception as e:
                print(f"Erreur lors du chargement du modèle: {e}")
                self.train_mock_model()
        else:
            print("Aucun modèle de tarification trouvé, création d'un modèle simulé")
            self.train_mock_model()
    
    def train_mock_model(self):
        """Entraîne un modèle simulé avec des données fictives"""
        # Créer des données d'entraînement fictives
        np.random.seed(42)
        
        # Caractéristiques: jours avant péremption (0-30), ratio stock/demande (0.1-5), 
        # catégorie (0-4), prix original (5-50)
        X_train = np.random.rand(200, 4)
        X_train[:, 0] = np.random.randint(0, 31, 200)  # jours avant péremption
        X_train[:, 1] = np.random.uniform(0.1, 5, 200)  # ratio stock/demande
        X_train[:, 2] = np.random.randint(0, 5, 200)    # catégorie
        X_train[:, 3] = np.random.uniform(5, 50, 200)   # prix original
        
        # Cible: pourcentage de réduction (0-0.9)
        y_train = np.zeros(200)
        
        # Logique de tarification simulée pour l'entraînement
        for i in range(200):
            days_to_expiry = X_train[i, 0]
            stock_demand_ratio = X_train[i, 1]
            
            # Base de réduction selon les jours avant péremption
            if days_to_expiry <= 1:
                reduction = 0.7
            elif days_to_expiry <= 3:
                reduction = 0.5
            elif days_to_expiry <= 7:
                reduction = 0.3
            elif days_to_expiry <= 14:
                reduction = 0.1
            else:
                reduction = 0.0
            
            # Ajustement selon le ratio stock/demande
            if stock_demand_ratio > 2.0:
                reduction += 0.1
            
            # Ajouter du bruit pour la variabilité
            reduction += np.random.normal(0, 0.05)
            
            # Limiter entre 0 et 0.9
            y_train[i] = max(0, min(0.9, reduction))
        
        # Entraîner le modèle
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Sauvegarder le modèle
        joblib.dump(self.model, self.model_path)
        print("Modèle de tarification simulé entraîné et sauvegardé")
    
    def calculate_price(self, product_id, expiry_date, stock_quantity, predicted_demand, 
                        original_price=10.0, category_id=0):
        """
        Calcule le prix réduit en fonction de la date de péremption et du stock
        
        Args:
            product_id: Identifiant du produit
            expiry_date: Date de péremption (format YYYY-MM-DD)
            stock_quantity: Quantité en stock
            predicted_demand: Demande prédite
            original_price: Prix original
            category_id: ID de la catégorie du produit
            
        Returns:
            Dictionnaire avec prix original, prix réduit, pourcentage de réduction et jours avant péremption
        """
        if not self.is_trained:
            self.train_mock_model()
        
        # Convertir la date de péremption
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")
        today = datetime.now()
        
        # Calculer les jours avant péremption
        days_to_expiry = max(0, (expiry_date - today).days)
        
        # Calculer le ratio stock/demande
        stock_demand_ratio = stock_quantity / max(predicted_demand, 1)
        
        # Caractéristiques pour la prédiction
        features = np.array([
            days_to_expiry,
            stock_demand_ratio,
            category_id,
            original_price
        ]).reshape(1, -1)
        
        # Prédire le pourcentage de réduction
        reduction = self.model.predict(features)[0]
        
        # Limiter entre 0 et 0.9
        reduction = max(0, min(0.9, reduction))
        
        # Calculer le prix réduit
        reduced_price = original_price * (1 - reduction)
        
        return {
            "identifiant_produit": product_id,
            "prix_original": original_price,
            "prix_reduit": round(reduced_price, 2),
            "pourcentage_reduction": round(reduction * 100, 1),
            "jours_avant_peremption": days_to_expiry
        }

# Créer une instance du modèle pour l'utiliser dans l'API
pricing_model = DynamicPricingModel()