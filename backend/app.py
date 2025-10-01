"""
Application principale EcoMarché pour la réduction du gaspillage alimentaire
"""
import os
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api

from config.constant import CORS_ORIGINS, APP_NAME, APP_VERSION, APP_DESCRIPTION
from config.db import db
from model.ecomarche_db import Produit, generer_donnees_test
from model.pricing_model import pricing_model
from resources.produits import ProduitsApi
from resources.risques import RisquesApi, predict_for_product
import pandas as pd
import joblib
import math
from flask import current_app

# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecomarche.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de l'API
api = Api(app)

# Initialisation de la base de données
db.init_app(app)
migrate = Migrate(app, db)

# Configuration CORS
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})

# Enregistrement des ressources API
api.add_resource(ProduitsApi, '/api/produits/<string:route>', endpoint='produits_all', methods=["GET", "POST"])
api.add_resource(ProduitsApi, '/api/produits/<string:route>', endpoint='produits_all_patch', methods=["PATCH", "DELETE"])

# ML risks endpoints
api.add_resource(RisquesApi, '/api/risques/<string:route>', endpoint='risques_reco', methods=["GET"])




# Servir le frontend Angular s'il existe
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    frontend_path = '../ecomarche-frontend/dist/ecomarche-frontend'
    
    if os.path.exists(frontend_path):
        # Si le fichier existe, le servir
        if path != "" and os.path.exists(os.path.join(frontend_path, path)):
            return send_from_directory(frontend_path, path)
        else:
            # Sinon servir index.html (routing Angular)
            return send_from_directory(frontend_path, 'index.html')
    else:
        # Si pas de frontend, page d'accueil simple
        return '''
        <html>
            <head><title>EcoMarché Dashboard</title></head>
            <body>
                <h1> EcoMarché Dashboard - Backend API</h1>
                <p>API Flask REST active </p>
                <h2>Endpoints disponibles :</h2>
                <ul>
                    <li><a href="/api/produits/all">/api/produits/all</a> - Liste des produits</li>
                    <li><a href="/api/kpi/overview">/api/kpi/overview</a> - KPIs globaux</li>
                    <li><a href="/api/kpi/waste_recommendations">/api/kpi/waste_recommendations</a> - Recommandations</li>
                    <li><a href="/api/sales/summary">/api/sales/summary</a> - Ventes</li>
                </ul>
                <p><em>Frontend Angular non disponible - mode API uniquement</em></p>
            </body>
        </html>
        '''





@app.route('/api/risques/predict/<int:produit_id>')
def api_predict_risk(produit_id):
    return predict_for_product(produit_id)

@app.route('/')
def home():
    """
    Page d'accueil de l'API
    """
    return jsonify({
        "message": f"Bienvenue sur l'API {APP_NAME} pour la réduction du gaspillage alimentaire",
        "version": APP_VERSION,
        "description": APP_DESCRIPTION
    })

def initialize_database():
    """
    Initialise la base de données et génère des données de test
    """
    with app.app_context():
        db.create_all()
        if Produit.query.count() == 0:
            generer_donnees_test()
        # Load sales dataset for visualization if available
        sales_csv = os.path.join(os.path.dirname(__file__), 'asstes', 'data', 'supermarche_historique_ventes.csv')
        try:
            current_app.sales_df = pd.read_csv(sales_csv, parse_dates=['Date'])
            print(f"Sales data loaded from {sales_csv} (rows={len(current_app.sales_df)})")
        except Exception as e:
            current_app.sales_df = None
            print(f"Sales data not loaded: {e}")
        # Load ML model (defensive). Path can be overridden with ML_MODEL_PATH env var
        try:
            from model.ml_model import RiskModel
            model_env = os.environ.get('ML_MODEL_PATH')
            default_model = os.path.join(os.path.dirname(__file__), 'model', 'saved_models', 'waste_predictor.joblib')
            model_path = model_env if model_env is not None else default_model
            current_app.risk_model = RiskModel.load(model_path)
            if current_app.risk_model.is_loaded():
                print(f"Loaded risk model from {model_path}")
            else:
                print(f"Risk model not loaded (path checked: {model_path})")
        except Exception as e:
            current_app.risk_model = None
            print(f"Failed to initialize risk model: {e}")


@app.route('/api/sales/summary')
def sales_summary():
    """Return a simple time series summary (daily total sales) for visualization."""
    df = getattr(current_app, 'sales_df', None)
    if df is None:
        return jsonify({'error': 'Sales dataset not available'}), 404
    daily = df.groupby(df['Date'].dt.date)['Daily_Sales'].sum().reset_index()
    # return last 90 days
    daily = daily.tail(90)
    return jsonify({ 'daily': daily.to_dict(orient='records') })


@app.route('/api/sales/top_products')
def sales_top_products():
    """Return top N products by total sales for simple visualization."""
    df = getattr(current_app, 'sales_df', None)
    if df is None:
        return jsonify({'error': 'Sales dataset not available'}), 404
    top = df.groupby('Product_Name')['Daily_Sales'].sum().reset_index().sort_values('Daily_Sales', ascending=False).head(10)
    return jsonify({ 'top_products': top.to_dict(orient='records') })


@app.route('/api/kpi/overview')
def kpi_overview():
    """Return key KPIs useful for decision-making: total revenue, avg daily sales, top categories."""
    df = getattr(current_app, 'sales_df', None)
    if df is None:
        return jsonify({'error': 'Sales dataset not available'}), 404

    # Ensure numeric
    df['Daily_Sales'] = pd.to_numeric(df['Daily_Sales'], errors='coerce').fillna(0)
    df['Unit_Price'] = pd.to_numeric(df['Unit_Price'], errors='coerce').fillna(0)

    # Total revenue (approx): sum(unit_price * daily_sales)
    df['Revenue'] = df['Unit_Price'] * df['Daily_Sales']
    total_revenue = float(df['Revenue'].sum())

    # Average daily sales (overall)
    daily = df.groupby(df['Date'].dt.date)['Daily_Sales'].sum().reset_index()
    avg_daily_sales = float(daily['Daily_Sales'].mean()) if len(daily) > 0 else 0.0

    # Top categories by sales
    if 'Category' in df.columns:
        top_categories = df.groupby('Category')['Daily_Sales'].sum().reset_index().sort_values('Daily_Sales', ascending=False).head(5)
        top_categories_records = top_categories.to_dict(orient='records')
    else:
        top_categories_records = []

    # Monthly series (last 12 months)
    df['YearMonth'] = df['Date'].dt.to_period('M').dt.to_timestamp()
    monthly = df.groupby('YearMonth')['Daily_Sales'].sum().reset_index().sort_values('YearMonth')
    monthly_series = monthly.tail(12).to_dict(orient='records')

    return jsonify({
        'total_revenue': total_revenue,
        'avg_daily_sales': avg_daily_sales,
        'top_categories': top_categories_records,
        'monthly_series': monthly_series
    })


@app.route('/api/sales/seasonality')
def sales_seasonality():
    """Return seasonality breakdown by month and by category for visualization."""
    df = getattr(current_app, 'sales_df', None)
    if df is None:
        return jsonify({'error': 'Sales dataset not available'}), 404

    df['Month'] = df['Date'].dt.month
    seasonality = df.groupby('Month')['Daily_Sales'].sum().reset_index().sort_values('Month')

    # optionally breakdown by top categories
    category_season = None
    if 'Category' in df.columns:
        top_cats = df.groupby('Category')['Daily_Sales'].sum().reset_index().sort_values('Daily_Sales', ascending=False).head(5)['Category'].tolist()
        cat_breakdown = df[df['Category'].isin(top_cats)].groupby(['Month','Category'])['Daily_Sales'].sum().reset_index()
        category_season = cat_breakdown.to_dict(orient='records')

    return jsonify({'seasonality_by_month': seasonality.to_dict(orient='records'), 'category_season': category_season})


@app.route('/api/sales/popular_by_season')
def sales_popular_by_season():
    """Return top products per season (DJF, MAM, JJA, SON)."""
    df = getattr(current_app, 'sales_df', None)
    if df is None:
        return jsonify({'error': 'Sales dataset not available'}), 404

    # define seasons by month
    def month_to_season(m):
        if m in [12,1,2]: return 'DJF'
        if m in [3,4,5]: return 'MAM'
        if m in [6,7,8]: return 'JJA'
        return 'SON'

    df['Month'] = df['Date'].dt.month
    df['Season'] = df['Month'].apply(month_to_season)

    grouped = df.groupby(['Season','Product_Name'])['Daily_Sales'].sum().reset_index()
    result = {}
    for season in ['DJF','MAM','JJA','SON']:
        top = grouped[grouped['Season']==season].sort_values('Daily_Sales', ascending=False).head(10)
        result[season] = top.to_dict(orient='records')

    return jsonify({'popular_by_season': result})


@app.route('/api/sales/by_age_groups')
def sales_by_age_groups():
    """Return sales aggregated by synthetic age groups when real demographics are not available.

    If the sales dataset contains user demographic columns, they should be used. Otherwise
    a simple deterministic split is returned to allow the dashboard to present age-based KPIs.
    """
    df = getattr(current_app, 'sales_df', None)
    if df is None:
        return jsonify({'error': 'Sales dataset not available'}), 404

    # Check for real demographic columns
    age_col = None
    for candidate in ['Age','User_Age','Customer_Age']:
        if candidate in df.columns:
            age_col = candidate
            break

    # Define age buckets
    age_buckets = ['18-25','26-45','46-65','65+']

    if age_col:
        df['age_bucket'] = pd.cut(df[age_col], bins=[0,25,45,65,200], labels=age_buckets, right=True)
        agg = df.groupby('age_bucket')['Daily_Sales'].sum().reset_index()
        overall = agg.to_dict(orient='records')
    else:
        # synthetic distribution: percentages
        total_sales = float(pd.to_numeric(df['Daily_Sales'], errors='coerce').fillna(0).sum())
        # deterministic distribution
        shares = [0.20, 0.45, 0.25, 0.10]
        overall = []
        for bucket, share in zip(age_buckets, shares):
            overall.append({'age_bucket': bucket, 'Daily_Sales': total_sales * share})

    # also provide top products with age split (synthetic)
    top_products = df.groupby('Product_Name')['Daily_Sales'].sum().reset_index().sort_values('Daily_Sales', ascending=False).head(10)
    top_products_list = []
    for _, row in top_products.iterrows():
        prod = row['Product_Name']
        sales = float(row['Daily_Sales'])
        # distribute sales across age groups proportionally but deterministic using hash
        h = abs(hash(prod))
        # create slight variation
        weights = [0.2 + ((h % 10) / 100.0), 0.45 - ((h % 7)/100.0), 0.25 + ((h % 5)/100.0), 0.10]
        svals = [sales * w / sum(weights) for w in weights]
        top_products_list.append({'product': prod, 'total_sales': sales, 'by_age': [{'age_bucket': b, 'sales': s} for b,s in zip(age_buckets, svals)]})

    return jsonify({'overall_by_age': overall, 'top_products_by_age': top_products_list})


@app.route('/api/kpi/waste_recommendations')
def waste_recommendations():
    """Compute a simple waste-risk score per product and return ranked recommendations.

    Drivers used:
    - expiry risk (jours_restants)
    - stock pressure (stock relative to recent avg daily sales)
    - price signal (price above median with low velocity)

    Returns top recommendations with a suggested action and discount.
    """
    df = getattr(current_app, 'sales_df', None)

    # compute some global stats from sales data when available
    if df is not None:
        df['Daily_Sales'] = pd.to_numeric(df['Daily_Sales'], errors='coerce').fillna(0)
        overall_daily = df.groupby(df['Date'].dt.date)['Daily_Sales'].sum().reset_index()
        overall_avg_daily = float(overall_daily['Daily_Sales'].mean()) if len(overall_daily) > 0 else 0.0
        # median unit price as a simple benchmark
        median_price = float(pd.to_numeric(df['Unit_Price'], errors='coerce').median()) if 'Unit_Price' in df.columns else 0.0
    else:
        overall_avg_daily = 0.0
        median_price = 0.0

    produits = Produit.query.all()
    recommendations = []
    eps = 1e-6

    def format_action_for_discount(discount):
        try:
            d = float(discount)
        except Exception:
            return 'Surveiller le stock (0%)'
        if d <= 0:
            return 'Surveiller le stock (0%)'
        if d >= 50:
            return f'Remise immédiate importante ({int(d)}%)'
        if d >= 40:
            return f'Remise immédiate importante ({int(d)}%)'
        if d >= 30:
            return f'Remise {int(d)}% ({int(d)}%)'
        if d >= 20:
            return f'Promotion multi-achat ({int(d)}%)'
        if d >= 10:
            return f'Petite promotion ({int(d)}%)'
        return f'Remise {int(d)}% ({int(d)}%)'

    for p in produits:
        prod_name = p.nom

        # estimate recent average daily sales for this product
        if df is not None and 'Product_Name' in df.columns:
            prod_df = df[df['Product_Name'] == prod_name]
            if len(prod_df) > 0:
                prod_daily = prod_df.groupby(prod_df['Date'].dt.date)['Daily_Sales'].sum().reset_index()
                prod_avg = float(prod_daily['Daily_Sales'].mean()) if len(prod_daily) > 0 else 0.0
            else:
                prod_avg = max(0.0, overall_avg_daily * 0.1)
        else:
            prod_avg = max(0.0, overall_avg_daily * 0.1)

        # expiry score: products expiring soon have higher score (30-day window)
        jr = p.jours_restants
        expiry_score = 0.0
        if jr is None:
            expiry_score = 0.0
        elif jr < 0:
            expiry_score = 1.0
        else:
            expiry_score = max(0.0, (30.0 - float(jr)) / 30.0) if jr < 30 else 0.0

        # stock score: ratio of stock to expected 7-day demand
        stock_ratio = float(p.stock) / (prod_avg * 7.0 + eps)
        stock_score = min(1.0, stock_ratio)

        # price score: penalize high price combined with low velocity
        price_score = 0.0
        unit_price = float(p.prix_unitaire) if p.prix_unitaire is not None else 0.0
        if median_price > 0:
            price_diff = max(0.0, (unit_price - median_price) / (median_price + eps))
            sales_ratio = prod_avg / (overall_avg_daily + eps) if overall_avg_daily > 0 else 0.0
            price_score = min(1.0, price_diff * (1.0 - sales_ratio))

        # composite risk score (weights tunable)
        heuristic_risk = 0.5 * expiry_score + 0.3 * stock_score + 0.2 * price_score

        # dominant driver
        drivers = {'expiry': expiry_score, 'stock': stock_score, 'price': price_score}
        driver = max(drivers.items(), key=lambda x: x[1])[0]

        # If a trained model is present, compute predicted risk probability and blend with heuristic
        model_prob = None
        try:
            model = getattr(current_app, 'waste_model', None)
            if model is not None:
                # Prepare the features expected by the minimal training script
                # Features: avg_daily_sales (approx prod_avg), price_rel (unit_price / median_price), sales_cv, days_present
                avg_daily_sales = prod_avg
                median_price = float(pd.to_numeric(df['Unit_Price'], errors='coerce').median()) if df is not None and 'Unit_Price' in df.columns else 1.0
                price_rel = unit_price / (median_price + 1e-6)
                sales_std = float(prod_df['Daily_Sales'].std()) if (df is not None and 'Product_Name' in df.columns and len(prod_df)>0) else 0.0
                sales_cv = sales_std / (avg_daily_sales + 1e-6)
                days_present = float(prod_df['Date'].nunique()) if (df is not None and 'Product_Name' in df.columns and len(prod_df)>0) else 0.0
                feat = [[avg_daily_sales, price_rel, sales_cv, days_present]]
                prob = None
                try:
                    prob = float(model.predict_proba(feat)[0][1]) if hasattr(model, 'predict_proba') else float(model.predict(feat)[0])
                except Exception:
                    # fallback if model expects other features
                    prob = None
                if prob is not None and (not math.isnan(prob)):
                    model_prob = max(0.0, min(1.0, prob))
        except Exception as e:
            model_prob = None

    # recommended action heuristics
        if driver == 'expiry':
            if jr is None:
                action = 'Vérifier date' 
                recommended_discount = 0
            elif jr <= 1:
                action = 'Remise immédiate importante'
                recommended_discount = 40
            elif jr <= 3:
                action = 'Remise 30%'
                recommended_discount = 30
            elif jr <= 7:
                action = 'Remise 15%'
                recommended_discount = 15
            else:
                action = 'Petite promotion (5%)'
                recommended_discount = 5
        elif driver == 'stock':
            if stock_ratio > 2.0:
                action = 'Promotion importante / bundle'
                recommended_discount = 30
            elif stock_ratio > 1.0:
                action = 'Promotion multi-achat'
                recommended_discount = 20
            else:
                action = 'Surveiller le stock'
                recommended_discount = 0
        else:
            action = 'Repositionner prix ou bundle pour accélérer ventes'
            recommended_discount = 15 if price_score > 0.2 else 10

        # If there is an active promotion persisted, prefer that value and label
        promotion = None
        try:
            promotion = p.get_active_promotion()
        except Exception:
            promotion = None

        if promotion:
            # override suggested discount and action with persisted promotion
            try:
                applied_discount = float(promotion.get('discount_percent', 0))
            except Exception:
                applied_discount = 0
            recommended_discount = applied_discount
            action = format_action_for_discount(applied_discount)

        recommendations.append({
            'product_id': p.id,
            'nom': prod_name,
            'stock': p.stock,
            'prix_unitaire': unit_price,
            'jours_restants': jr,
            'expiry_score': round(expiry_score, 3),
            'stock_score': round(stock_score, 3),
            'price_score': round(price_score, 3),
            # Provide both heuristic and (if available) model probability
            'risk_score': round(heuristic_risk, 3),
            'model_risk_prob': round(model_prob, 3) if model_prob is not None else None,
            'blended_risk': round((model_prob * 0.7 + heuristic_risk * 0.3) if model_prob is not None else heuristic_risk, 3),
            'driver': driver,
            'recommended_action': action,
            'recommended_discount': recommended_discount,
            'promotion': promotion
        })

    recommendations_sorted = sorted(recommendations, key=lambda x: x['risk_score'], reverse=True)
    return jsonify({'recommendations': recommendations_sorted[:20]})


@app.route('/api/produits/<int:produit_id>/apply_discount', methods=['POST'])
def apply_discount(produit_id):
    """Apply a discount percentage to a produit's prix_unitaire and persist it.

    Request JSON: { "discount_percent": 20 }
    Returns updated produit dict.
    """
    data = request.get_json() or {}
    discount = float(data.get('discount_percent', 0))
    if discount <= 0:
        return jsonify({'error': 'discount_percent must be > 0'}), 400

    produit = Produit.query.get(produit_id)
    if not produit:
        return jsonify({'error': 'Produit not found'}), 404

    # Create a Promotion record instead of changing base price
    try:
        from model.ecomarche_db import Promotion
        prom = Promotion(
            produit_id=produit.id,
            discount_percent=discount,
            start_date=None,
            end_date=None,
            active=True
        )
        db.session.add(prom)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    # return product with active promotion included
    return jsonify({'status': 'success', 'produit': produit.to_dict(), 'promotion': prom.to_dict()})

# Exécuter l'initialisation au démarrage
initialize_database()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)