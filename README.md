# EcoMarché Dashboard

Un tableau de bord pédagogique pour réduire le gaspillage alimentaire en magasin.

Ce dépôt contient :
- Un backend Flask + SQLAlchemy (dossier `backend/`) qui expose une API REST pour gérer les produits, calculer des KPIs et générer des recommandations pour réduire le gaspillage.
- Un frontend Angular (dossier `ecomarche-frontend/`) qui affiche les KPIs, visualisations et une interface pour appliquer les recommandations (promotions).

## Objectif de l'application
L'objectif pédagogique et d'évaluation est clair : identifier les "Produits à risque de gaspillage", expliquer pourquoi (causes) et proposer des actions opérationnelles priorisées pour réduire le gaspillage (p.ex. promotions, remises, bundles).

Le projet aide à démontrer la capacité à :
- fusionner données de stock produit et historique de ventes,
- détecter des signaux de gaspillage (péremption, surstock, manque de rotation dû au prix),
- proposer des actions priorisées et persistantes (promotions) et mesurer l'impact.

## Principes de fonctionnement (haute-niveau)
- Données produit : table `produits` (modèle `Produit`) contient `stock`, `prix_unitaire`, `date_peremption`, etc.
- Données ventes : un CSV d'historique est chargé au démarrage (si présent) et utilisé pour estimer la demande par produit, les prix médians, et la saisonnalité.
- Recommandation : pour chaque produit le backend calcule des scores (expiry_score, stock_score, price_score) puis un `risk_score` composite. Le driver dominant (expiry/stock/price) est retourné avec une action recommandée et un pourcentage de remise.
- Application d'une recommandation : l'action (remise) est persistée dans une table `promotions` (audit/traçabilité) — le prix de base n'est pas écrasé.

## Endpoints clés (exemples)
- GET /api/produits/all — lister les produits
- POST /api/produits/create — créer un produit
- POST /api/produits/<id>/apply_discount — appliquer une promotion (body: { discount_percent: number })
- GET /api/kpi/waste_recommendations — liste priorisée des recommandations (risk_score, drivers, action, discount)
- GET /api/kpi/overview — KPIs globaux (CA total, ventes moy. journalières, top catégories)
- GET /api/sales/summary — séries temporelles des ventes (daily)
- GET /api/sales/top_products — top produits par ventes
- GET /api/sales/seasonality — saisonnalité par mois
- GET /api/sales/popular_by_season — top produits par saison
- GET /api/sales/by_age_groups — agrégation synthétique par tranche d'âge (si données démographiques absentes)

## Installation & exécution (local)
Prerequis : Python 3.10+, Node.js 16+, npm

1. Backend

```powershell
# depuis le dossier backend
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

Le backend écoute par défaut sur http://127.0.0.1:8000

2. Frontend

```cmd
# depuis le dossier ecomarche-frontend
npm install
npm start
```

Ouvrez ensuite http://localhost:4200

## Comment le système aide à réduire le gaspillage (explication pour l'évaluation)
1. Identification : le backend calcule un score de risque par produit combinant péremption, stock et prix. Cela transforme des données brutes en priorités exploitables.
2. Diagnostic : pour chaque produit on fournit le driver dominant (ex. "expiry" ou "stock") — cela permet d'adapter l'action (remise urgente vs promotion multi-achat).
3. Action persistante : en cliquant "Appliquer remise" dans le dashboard, la remise est enregistrée (table `promotions`), ce qui permet d'auditer et d'analyser l'impact.
4. Mesure : les endpoints KPI et les séries de ventes permettent d'observer l'évolution après intervention (à compléter par instrumentation d'impact dans la vraie prod).

## Recommandations techniques (pour production)
- Ne pas écraser `prix_unitaire` : utiliser une entité `Promotion` (déjà implémentée) pour gérer promotions temporaires.
- Ajouter gestion des dates (début/fin), annulation et règles de priorité (ex. éviter promotions concurrentes incompatibles).
- Ajouter logs et métriques (A/B testing pour mesurer impact des promotions).
- Ajouter tests automatisés (unit + integration) et CI (build frontend, tests backend).
- Protéger les endpoints applicatifs (auth/authz) avant déploiement.

## Commandes utiles
Voir recommandations :

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/kpi/waste_recommendations' -UseBasicParsing | ConvertTo-Json -Depth 5
```

Appliquer promotion (ex. 20% sur produit id=1) :

```powershell
Invoke-RestMethod -Method POST -Uri 'http://127.0.0.1:8000/api/produits/1/apply_discount' -ContentType 'application/json' -Body (ConvertTo-Json @{ discount_percent=20 }) -UseBasicParsing | ConvertTo-Json -Depth 5
```

## Limitations actuelles
- Scoring heuristique — il faut calibrer les poids et valider sur données historiques.
- Pas de gestion avancée des promotions (durée, ciblage, annulation) — prévu en amélioration.
- L'interface est en mode démonstration : surveillez les journaux et la base pour valider les actions.

---

Si vous voulez, je peux :
- ajouter une migration (Flask-Migrate) pour créer la table `promotions` et vous montrer comment l'appliquer localement ;
- ajouter une petite interface d'historique des promotions dans le dashboard ;
- ajouter un script e2e (Python) qui automatise création → recommandation → application → vérification.

Dites-moi quelle option vous préférez et je l'ajoute.
