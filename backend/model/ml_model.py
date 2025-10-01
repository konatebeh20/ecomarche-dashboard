import os
import joblib
import math
from typing import Optional, Any, List


class RiskModel:
    """Wrapper around a scikit-learn-like model to provide safe prediction helpers.

    The loader is defensive: if the model file is missing or fails to load, calls
    to predict will return None.
    """

    def __init__(self, model: Optional[Any]):
        self.model = model

    @staticmethod
    def load(path: Optional[str] = None):
        if path is None:
            return RiskModel(None)
        try:
            if not os.path.exists(path):
                return RiskModel(None)
            m = joblib.load(path)
            return RiskModel(m)
        except Exception:
            return RiskModel(None)

    def is_loaded(self) -> bool:
        return self.model is not None

    def predict_proba(self, X: List[List[float]]) -> Optional[List[float]]:
        try:
            if self.model is None:
                return None
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)
                # return probability of positive class
                return [float(p[1]) for p in proba]
            # fallback to predict (may return score)
            preds = self.model.predict(X)
            return [float(p) for p in preds]
        except Exception:
            return None

    def predict(self, X: List[List[float]]) -> Optional[List[float]]:
        try:
            if self.model is None:
                return None
            preds = self.model.predict(X)
            return [float(p) for p in preds]
        except Exception:
            return None

    @staticmethod
    def build_features_for_product(product, sales_df):
        """Build a minimal feature vector used by the deployed model.

        Features (compatible with the minimal training script):
          - avg_daily_sales
          - price_rel (unit_price / median_price)
          - sales_cv (coefficient of variation)
          - days_present

        Returns a list of floats [avg_daily_sales, price_rel, sales_cv, days_present]
        """
        try:
            # average daily sales estimate
            prod_name = product.nom
            if sales_df is not None and 'Product_Name' in sales_df.columns:
                prod_df = sales_df[sales_df['Product_Name'] == prod_name]
                if len(prod_df) > 0:
                    prod_daily = prod_df.groupby(prod_df['Date'].dt.date)['Daily_Sales'].sum().reset_index()
                    avg_daily = float(prod_daily['Daily_Sales'].mean()) if len(prod_daily) > 0 else 0.0
                    sales_std = float(prod_daily['Daily_Sales'].std()) if len(prod_daily) > 0 else 0.0
                    days_present = float(prod_df['Date'].nunique())
                else:
                    avg_daily = 0.0
                    sales_std = 0.0
                    days_present = 0.0
            else:
                avg_daily = 0.0
                sales_std = 0.0
                days_present = 0.0

            median_price = 1.0
            if sales_df is not None and 'Unit_Price' in sales_df.columns:
                try:
                    median_price = float(sales_df['Unit_Price'].median())
                except Exception:
                    median_price = 1.0

            unit_price = float(product.prix_unitaire) if product.prix_unitaire is not None else 0.0
            price_rel = unit_price / (median_price + 1e-6)
            sales_cv = (sales_std / (avg_daily + 1e-6)) if avg_daily > 0 else 0.0

            return [avg_daily, price_rel, sales_cv, days_present]
        except Exception:
            return [0.0, 0.0, 0.0, 0.0]
