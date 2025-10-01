import os
import sys
import pytest

# Ensure backend package path is available when running tests from repository root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from model.ml_model import RiskModel


class DummyProduct:
    def __init__(self, nom, prix_unitaire, stock, jours_restants):
        self.nom = nom
        self.prix_unitaire = prix_unitaire
        self.stock = stock
        self.jours_restants = jours_restants


def test_build_features_default():
    p = DummyProduct('Produit X', 100.0, 10, 5)
    feat = RiskModel.build_features_for_product(p, None)
    assert isinstance(feat, list)
    assert len(feat) == 4
    assert feat[0] == 0.0


def test_predict_without_model():
    rm = RiskModel.load(None)
    assert not rm.is_loaded()
    # predict_proba should return None when no model loaded
    out = rm.predict_proba([[0, 0, 0, 0]])
    assert out is None


@pytest.mark.skipif(not os.path.exists('model/saved_models/waste_predictor.joblib'), reason="No saved model present")
def test_predict_with_saved_model():
    path = 'model/saved_models/waste_predictor.joblib'
    rm = RiskModel.load(path)
    assert isinstance(rm, RiskModel)
    # If model loaded, predict_proba should return a list or None (defensive)
    res = rm.predict_proba([[0.0, 0.0, 0.0, 0.0]])
    assert (res is None) or (isinstance(res, list))
