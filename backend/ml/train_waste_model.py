"""
Minimal training script for a waste-prediction model (RandomForest) using historical sales CSV as a data source.
- Produces a proxy label if explicit waste labels are not present.
- Logs the run with MLflow (if installed) and saves a joblib model to backend/model/saved_models/

Usage:
    python train_waste_model.py

Notes:
- This is a minimal POC. For production you should add proper feature engineering, cross-validation
  and label quality checks.
"""
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
import joblib

try:
    import mlflow
    MLFLOW_AVAILABLE = True
except Exception:
    MLFLOW_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'asstes', 'data', 'supermarche_historique_ventes.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'model', 'saved_models')
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, 'waste_predictor.joblib')

def load_sales():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Sales data not found at {DATA_PATH}")
    df = pd.read_csv(DATA_PATH, parse_dates=['Date'])
    return df


def build_features_and_label(df):
    """Build simple per-product features and a proxy label.

    Proxy label logic (if explicit label absent):
    - For each product and each date we compute cumulative sales until the product's nearest future expiration
      (if expiration known in product table it's better; here we approximate).
    - Simpler approach: label product-month as 'waste' if average daily sales in the next 7 days is below a small threshold
      AND the item had positive stock (we approximate by observing days with sales==0).

    For this POC we aggregate at product level using statistics across the dataset.
    """
    # Aggregate product-level stats
    df['Daily_Sales'] = pd.to_numeric(df.get('Daily_Sales', 0), errors='coerce').fillna(0)
    df['Unit_Price'] = pd.to_numeric(df.get('Unit_Price', 0), errors='coerce').fillna(0)

    grouped = df.groupby('Product_Name').agg(
        avg_daily_sales=('Daily_Sales', 'mean'),
        median_price=('Unit_Price', 'median'),
        std_daily_sales=('Daily_Sales', 'std'),
        max_daily_sales=('Daily_Sales', 'max'),
        days_present=('Date', 'nunique')
    ).reset_index()

    # proxy label: mark products with very low avg_daily_sales and low max_daily_sales as at-risk of waste
    grouped['label_waste'] = ((grouped['avg_daily_sales'] < 0.5) & (grouped['max_daily_sales'] < 2)).astype(int)

    # feature: relative price (normalized by global median)
    global_median_price = grouped['median_price'].median() if len(grouped) > 0 else 1.0
    grouped['price_rel'] = grouped['median_price'] / (global_median_price + 1e-6)
    grouped['sales_cv'] = grouped['std_daily_sales'] / (grouped['avg_daily_sales'] + 1e-6)
    grouped['days_present'] = grouped['days_present']

    # Keep only rows with non-null median_price
    dataset = grouped.dropna(subset=['median_price'])
    features = dataset[['avg_daily_sales', 'price_rel', 'sales_cv', 'days_present']]
    labels = dataset['label_waste']
    names = dataset['Product_Name']
    return features, labels, names


def train_and_save(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if len(set(y))>1 else None)
    clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    proba = clf.predict_proba(X_test)[:,1] if hasattr(clf, 'predict_proba') else None
    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, proba) if proba is not None and len(set(y_test))>1 else None

    # log with mlflow if available
    if MLFLOW_AVAILABLE:
        mlflow.sklearn.log_model(clf, "waste_predictor")
        mlflow.log_metric('accuracy', float(acc))
        if auc is not None:
            mlflow.log_metric('roc_auc', float(auc))

    # save joblib
    joblib.dump(clf, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Accuracy: {acc:.4f}")
    if auc is not None:
        print(f"ROC AUC: {auc:.4f}")


def main():
    print("Loading sales data...")
    df = load_sales()
    print("Building features and label...")
    X, y, names = build_features_and_label(df)
    print(f"Dataset size: {len(X)}")
    if len(X) < 10:
        print("WARNING: very small dataset for training — results may be poor")
    print("Training model...")
    if MLFLOW_AVAILABLE:
        with mlflow.start_run():
            train_and_save(X, y)
    else:
        train_and_save(X, y)


if __name__ == '__main__':
    main()
