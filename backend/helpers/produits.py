"""
Logique métier pour la gestion des produits
"""
from flask import request, jsonify
from datetime import datetime
from config.db import db
from model.ecomarche_db import Produit
from model.pricing_model import pricing_model

def get_all_produits():
    """
    Récupère tous les produits de la base de données
    """
    response = {}
    try:
        produits = Produit.query.all()
        produits_list = [produit.to_dict() for produit in produits]
        
        response['status'] = 'success'
        response['produits'] = produits_list
    except Exception as e:
        response['status'] = 'error'
        response['error_description'] = str(e)
    
    return response

def get_produit_by_id(produit_id):
    """
    Récupère un produit par son ID
    """
    response = {}
    try:
        produit = Produit.query.filter_by(id=produit_id).first()
        
        if produit:
            response['status'] = 'success'
            response['produit'] = produit.to_dict()
        else:
            response['status'] = 'error'
            response['error_description'] = 'Produit non trouvé'
    except Exception as e:
        response['status'] = 'error'
        response['error_description'] = str(e)
    
    return response

def create_produit():
    """
    Crée un nouveau produit
    """
    response = {}
    try:
        # Récupérer les données du produit depuis la requête
        data = request.json
        
        # Convertir la date de péremption en objet date
        date_peremption = None
        if data.get('date_peremption'):
            date_peremption = datetime.fromisoformat(data['date_peremption']).date()
        
        # Créer le produit
        produit = Produit(
            nom=data['nom'],
            categorie_id=data['categorie_id'],
            stock=data['stock'],
            prix_unitaire=data['prix_unitaire'],
            fournisseur=data['fournisseur'],
            date_peremption=date_peremption
        )
        
        # Ajouter le produit à la base de données
        db.session.add(produit)
        db.session.commit()
        
        response['status'] = 'success'
        response['produit'] = produit.to_dict()
    except Exception as e:
        db.session.rollback()
        response['status'] = 'error'
        response['error_description'] = str(e)
    
    return response

def update_produit(produit_id):
    """
    Met à jour un produit existant
    """
    response = {}
    try:
        # Récupérer le produit
        produit = Produit.query.filter_by(id=produit_id).first()
        
        if not produit:
            response['status'] = 'error'
            response['error_description'] = 'Produit non trouvé'
            return response
        
        # Récupérer les données du produit depuis la requête
        data = request.json
        
        # Mettre à jour les attributs du produit
        if 'nom' in data:
            produit.nom = data['nom']
        if 'categorie_id' in data:
            produit.categorie_id = data['categorie_id']
        if 'stock' in data:
            produit.stock = data['stock']
        if 'prix_unitaire' in data:
            produit.prix_unitaire = data['prix_unitaire']
        if 'fournisseur' in data:
            produit.fournisseur = data['fournisseur']
        if 'date_peremption' in data and data['date_peremption']:
            produit.date_peremption = datetime.fromisoformat(data['date_peremption']).date()
        
        # Sauvegarder les modifications
        db.session.commit()
        
        response['status'] = 'success'
        response['produit'] = produit.to_dict()
    except Exception as e:
        db.session.rollback()
        response['status'] = 'error'
        response['error_description'] = str(e)
    
    return response

def delete_produit(produit_id):
    """
    Supprime un produit
    """
    response = {}
    try:
        # Récupérer le produit
        produit = Produit.query.filter_by(id=produit_id).first()
        
        if not produit:
            response['status'] = 'error'
            response['error_description'] = 'Produit non trouvé'
            return response
        
        # Supprimer le produit
        db.session.delete(produit)
        db.session.commit()
        
        response['status'] = 'success'
        response['message'] = f'Produit {produit_id} supprimé avec succès'
    except Exception as e:
        db.session.rollback()
        response['status'] = 'error'
        response['error_description'] = str(e)
    
    return response

def predict_demand():
    """
    Endpoint de prédiction désactivé.
    Cette API était utilisée pour prévoir la demande. La fonctionnalité a été
    retirée côté frontend : renvoyer une réponse explicite 410 (Gone).
    """
    response = {
        'status': 'error',
        'error_description': 'La fonctionnalité de prédiction de la demande a été désactivée',
    }
    return (response, 410)

def calculate_pricing():
    """
    Calcule la tarification dynamique
    """
    response = {}
    try:
        data = request.json
        product_id = data.get('product_id')
        
        # Vérifier si le produit existe
        produit = Produit.query.filter_by(id=product_id).first()
        if not produit:
            response['status'] = 'error'
            response['error_description'] = 'Produit non trouvé'
            return response
        
        # Utiliser le modèle de tarification
        pricing_result = pricing_model.calculate_price(
            product_id=product_id,
            expiry_date=data.get('date_peremption', produit.date_peremption.isoformat() if produit.date_peremption else None),
            stock_quantity=data.get('stock', produit.stock),
            predicted_demand=data.get('prevision_demande', 0),
            original_price=data.get('prix_original', produit.prix_unitaire),
            category_id=data.get('categorie_id', produit.categorie_id)
        )
        
        response['status'] = 'success'
        response.update(pricing_result)
    except Exception as e:
        response['status'] = 'error'
        response['error_description'] = str(e)
    
    return response