"""
API endpoints pour la gestion des produits
"""
from flask_restful import Resource
from helpers.produits import (
    get_all_produits, 
    get_produit_by_id, 
    create_produit, 
    update_produit, 
    delete_produit,
    predict_demand,
    calculate_pricing
)

class ProduitsApi(Resource):
    def get(self, route):
        """
        Gère les requêtes GET pour les produits
        """
        if route == 'all':
            return get_all_produits()
        elif route.isdigit():
            return get_produit_by_id(int(route))
        else:
            return {"status": "error", "error_description": "Route non valide"}, 400
    
    def post(self, route):
        """
        Gère les requêtes POST pour les produits
        """
        if route == 'create':
            return create_produit()
        elif route == 'predict':
            # Endpoint de prédiction désactivé — renvoyer 410 Gone pour indiquer
            # que la fonctionnalité n'est plus disponible.
            return ({'status': 'error', 'error_description': 'La fonctionnalité de prédiction de la demande a été désactivée'}, 410)
        elif route == 'pricing':
            return calculate_pricing()
        else:
            return {"status": "error", "error_description": "Route non valide"}, 400
    
    def patch(self, route):
        """
        Gère les requêtes PATCH pour les produits
        """
        if route.isdigit():
            return update_produit(int(route))
        else:
            return {"status": "error", "error_description": "Route non valide"}, 400
    
    def delete(self, route):
        """
        Gère les requêtes DELETE pour les produits
        """
        if route.isdigit():
            return delete_produit(int(route))
        else:
            return {"status": "error", "error_description": "Route non valide"}, 400