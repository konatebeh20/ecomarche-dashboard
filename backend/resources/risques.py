from flask import current_app, jsonify
from flask_restful import Resource
from model.ecomarche_db import Produit
from model.ml_model import RiskModel


class RisquesApi(Resource):
    """Endpoints pour l'inférence de risque de gaspillage.

    Routes:
      - /api/risques/recommandations  (GET)
      - /api/risques/predict/<int:produit_id> (GET)
    """

    def get(self, route=None, produit_id=None):
        # route dispatcher
        if route == 'recommandations':
            return self._recommandations()
        return jsonify({'error': 'unknown route'}), 404

    def _recommandations(self):
        produits = Produit.query.all()
        sales_df = getattr(current_app, 'sales_df', None)
        model: RiskModel = getattr(current_app, 'risk_model', None)
        results = []
        for p in produits:
            feat = RiskModel.build_features_for_product(p, sales_df)
            model_prob = None
            if model is not None and model.is_loaded():
                proba = model.predict_proba([feat])
                if proba is not None:
                    model_prob = round(proba[0], 3)

            # reuse existing heuristic in app.py's waste_recommendations if desired
            results.append({
                'product_id': p.id,
                'nom': p.nom,
                'stock': p.stock,
                'prix_unitaire': p.prix_unitaire,
                'jours_restants': p.jours_restants,
                'model_risk_prob': model_prob
            })

        # sort by model probability when available else by stock/jours_restants
        results_sorted = sorted(results, key=lambda x: x['model_risk_prob'] if x['model_risk_prob'] is not None else 0.0, reverse=True)
        return jsonify({'recommendations': results_sorted})


def predict_for_product(produit_id: int):
    p = Produit.query.get(produit_id)
    if not p:
        return jsonify({'error': 'Produit not found'}), 404
    sales_df = getattr(current_app, 'sales_df', None)
    model: RiskModel = getattr(current_app, 'risk_model', None)
    feat = RiskModel.build_features_for_product(p, sales_df)
    if model is None or not model.is_loaded():
        return jsonify({'error': 'Model not loaded'}), 503
    proba = model.predict_proba([feat])
    if proba is None:
        return jsonify({'error': 'Prediction failed'}), 500
    return jsonify({'product_id': produit_id, 'risk_prob': round(proba[0], 4)})
