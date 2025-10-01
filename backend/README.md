# Backend — ecomarche-dashboard

Ce document explique comment configurer, exécuter et développer la partie backend de l'application `ecomarche-dashboard` (API Flask + SQLAlchemy). Il contient les commandes courantes pour Windows (cmd.exe), les endpoints principaux, les scripts utilitaires et des conseils de debug.

## Vue d'ensemble

- Technologie : Python 3.11+, Flask, Flask-RESTful, Flask-SQLAlchemy, Flask-Migrate
- Emplacement du code : `backend/`
- Principaux fichiers :
  - `backend/app.py` — point d'entrée de l'application
  - `backend/resources/produits.py` — routes REST pour les produits
  - `backend/helpers/produits.py` — logique métier (CRUD, pricing, promotions)
  - `backend/model/ecomarche_db.py` — modèles SQLAlchemy (`Produit`, `Promotion`)
  - `backend/requirements.txt` — dépendances Python
  - `backend/asstes/data/supermarche_historique_ventes.csv` — dataset des ventes
  - `backend/scripts/` — scripts utilitaires (scraping, comparaison de prix)

Important : le champ `date_peremption` est central pour la logique métier (produits "à risque"). Ne pas renommer ce champ sans synchroniser frontend et backend.

## Installation (Windows / cmd.exe)

1. Créez et activez un environnement virtuel :

```batch
cd backend
python -m venv venv
venv\Scripts\activate.bat
```

2. Installez les dépendances :

```batch
pip install -r requirements.txt
```

3. Initialiser / appliquer les migrations (optionnel si `instance/ecomarche.db` existe) :

```batch
rem Assurez-vous que FLASK_APP pointe vers backend/app.py
set FLASK_APP=app.py
flask db init        rem seulement la première fois
flask db migrate -m "init"
flask db upgrade
```

> Note : si vous préférez, l'application peut démarrer sans migrations si une base SQLite pré-remplie existe (`instance/ecomarche.db`).

## Lancer l'API

Depuis `backend/` (avec l'environnement activé) :

```batch
python app.py
```

Par défaut l'API écoute sur `http://localhost:8000/`.

## Endpoints principaux

La ressource des produits utilise un route token `route` (ex : `/api/produits/all`, `/api/produits/create`, `/api/produits/pricing`) — voir `backend/resources/produits.py`.

Endpoints utiles :

- GET /api/produits/all
  - Retourne la liste complète des produits (format JSON). Exemple :
    - { status: "success", produits: [ { id, nom, prix_unitaire, stock, date_peremption, ...}, ... ] }

- POST /api/produits/create
  - Crée un produit (payload JSON attendu : `nom`, `prix_unitaire`, `stock`, `date_peremption`, ...)

- PATCH /api/produits/<id>
  - Mise à jour partielle d'un produit. Exemple body : `{ "prix_unitaire": 250.0, "stock": 12, "date_peremption": "2025-10-01" }`

- POST /api/produits/<id>/apply_discount  (ou équivalent selon route token)
  - Applique et persiste une promotion pour audit (persistée dans le modèle `Promotion`).

Notes :
- Le backend est traité comme source de vérité pour les prix affichés par le frontend. Le frontend a été modifié pour utiliser `prix_unitaire` provenant de l'API et masquer les prix nuls/à 0.
- La fonctionnalité de prédiction de la demande est désactivée / marquée comme obsolète dans le code (retours 410/placeholder). Si besoin de réactiver, mettre à jour `backend/helpers/produits.py` et l'API frontend.

## Scripts utilitaires

Les scripts utiles se trouvent dans `backend/scripts/` :

- `scrape_prices.py`
  - Scraper léger (requests + BeautifulSoup) pour détecter prix publics sur des enseignes (ex : Jumia, Auchan).
  - Options typiques : `--dry-run`, `--products "Prod1,Prod2"`, `--out-csv <path>`, `--max-price <value>`.
  - Utilisé pour produire `supermarche_historique_ventes.prix_detecte.csv` qui complète le dataset original.
  - Exemple (dry-run) :

```batch
cd backend
venv\Scripts\activate.bat
python scripts\scrape_prices.py --dry-run --products "Pommes Golden,Tomates,Bananes"
```

- `compare_prices.py`
  - Compare les prix stockés dans l'API (/api/produits/all) avec les prix présents dans `backend/asstes/data/supermarche_historique_ventes.csv`.
  - Utilise `difflib` pour fuzzy-match des noms produits et résume les `most_common` détectés.

Exemple d'exécution :

```batch
cd backend
venv\Scripts\activate.bat
python scripts\compare_prices.py
```

## Données

- `backend/asstes/data/supermarche_historique_ventes.csv` : dataset historique (source principale pour les prix)
- `backend/asstes/data/supermarche_historique_ventes.prix_detecte.csv` : fichier produit par le scraper contenant colonnes additionnelles `prix_detecte`, `unite_detectee`, `source_url` (après exécution non-dry-run du scraper).

Conseil : vérifier manuellement les cas ambigus (ex : unités kg vs pièce) avant d'appliquer des mises à jour en masse au backend.

## Exemples d'appels API (curl / Windows cmd)

Récupérer tous les produits :

```batch
curl -X GET "http://localhost:8000/api/produits/all"
```

Mettre à jour le prix d'un produit (PATCH) :

```batch
curl -X PATCH "http://localhost:8000/api/produits/8" -H "Content-Type: application/json" -d "{ \"prix_unitaire\": 250.0 }"
```

Appliquer une promotion (exemple) :

```batch
curl -X POST "http://localhost:8000/api/produits/8/apply_discount" -H "Content-Type: application/json" -d "{ \"remise_pct\": 20, \"raison\": \"Fin de série\" }"
```

## Développement & Debug

- Activez le venv et exécutez `python app.py`. Sur erreurs d'import, vérifiez l'environnement virtuel et que `requirements.txt` a bien été installé.
- Vérifiez la présence du fichier SQLite `instance/ecomarche.db` si vous ne voulez pas exécuter les migrations.
- Si un champ `prix_unitaire` pose problème (valeurs 0.0 usagées comme sentinel), considérez une migration pour autoriser `NULL` et nettoyer les sentinelles.
- Pour le scraping : les résultats peuvent être bruyants (pages de recherche, formats variés). Préférez les pages produit détaillées quand possible et validez manuellement les résultats avant application en base.

## Tests et smoke checks

Aucun test automatisé n'est inclus pour le moment. Smoke checks recommandés :

- Après démarrage :

```batch
curl -X GET "http://localhost:8000/api/produits/all"  
rem Vérifier la présence d'une liste JSON de produits
```

- Après avoir appliqué une modification :

```batch
curl -X PATCH "http://localhost:8000/api/produits/13" -H "Content-Type: application/json" -d "{ \"prix_unitaire\": 3.0 }"
curl -X GET "http://localhost:8000/api/produits/13"  rem (si endpoint existe) ou relire /api/produits/all
```

## Conseils pour la production / MLOps (bref)

- Versionner les datasets (DVC ou simple timestamped CSV) avant d'appliquer changements automatiques.
- Préférer un pipeline de validation manuelle (relecture humaine) pour les mises à jour de prix provenant du scraper.
- Externaliser les modèles ML (joblib) et les surveiller (drift) si vous réactivez la prédiction de demande.

### Intégration ML & MLOps (recommandé)

Ce backend contient désormais des primitives pour déployer et servir un modèle ML qui estime le risque de gaspillage par produit. Voici les points clés pour opérer le modèle et intégrer des pratiques MLOps :

- Emplacement du modèle actif : `backend/model/saved_models/` (ex : `waste_risk_model_v1.joblib`).
- Chargement au démarrage : l'API charge le modèle à l'initialisation via la variable d'environnement `ML_MODEL_PATH`. Si non définie, elle essaie `backend/model/saved_models/waste_predictor.joblib`.
- Wrapper ML : `backend/model/ml_model.py` expose `RiskModel` qui encapsule le modèle joblib et fournit `predict_proba` et un helper `build_features_for_product`.

Endpoints ML ajoutés :

- GET `/api/risques/recommandations`
  - Récupère la liste des produits, calcule les features pour chacun et retourne un `model_risk_prob` (si modèle chargé) pour prioriser les actions.

- GET `/api/risques/predict/<id>`
  - Retourne la probabilité de risque pour un produit précis (ou un code 503 si le modèle n'est pas chargé).

Processus de versionning et déploiement du modèle

1. Entraînement (hors backend) : le pipeline training (ex : un notebook ou un script CI) produit un fichier `waste_risk_model_vX.joblib` et le stocke dans un artefact/versionnement (DVC, MLFlow/artifacts, ou stockage cloud).
2. Validation : exécutez une suite de tests pytest (incluant tests d'inférence smoke) et des validations manuelles (examen d'échantillons) avant déploiement.
3. Déploiement : le pipeline CI/CD copie le nouveau joblib dans `backend/model/saved_models/` ou met à jour un storage accessible et définit `ML_MODEL_PATH` sur le nouvel artefact ; puis redéployez (ou redémarrez) l'API pour charger le nouveau modèle.

Conseils pratiques

- Séparez le training (offline) et l'inférence (runtime). Le backend doit se limiter à charger un artefact stable.
- Conservez des versions immuables du modèle (nommer avec `vX` + timestamp). Cela permet de revenir en arrière si besoin.
- Ajoutez des tests pytest qui valident que `RiskModel.load` charge l'artefact attendu et que `predict_proba` renvoie des valeurs dans [0,1] pour quelques cas fixture.
- Monitorer la distribution des features en production (via logs ou métriques) pour détecter le drift et planifier ré-entraînement.

Exemple d'utilisation locale / test

```batch
cd backend
venv\Scripts\activate.bat
set ML_MODEL_PATH=backend\model\saved_models\waste_risk_model_v1.joblib
python app.py
curl -X GET "http://localhost:8000/api/risques/recommandations"
curl -X GET "http://localhost:8000/api/risques/predict/13"
```


## Contribution

- Forkez, créez une branche et ouvrez une PR pour les changements. Tests manuels et smoke-run demandés pour toute modification qui affecte le schéma DB ou l'API.

## Questions fréquentes / Troubleshooting rapide

- "L'API ne démarre pas" — Vérifiez que votre venv est activé et que `requirements.txt` est installé.
- "Les prix s'affichent comme 0" — Le frontend masque 0; cela peut indiquer une absence de prix réel en base (sentinel). Envisagez une migration pour permettre `NULL`.
- "Scraper retourne des valeurs absurdes" — Les pages de recherche sont bruyantes; inspectez `backend/asstes/data/supermarche_historique_ventes.prix_detecte.csv` pour valider les `source_url` et échantillons.

---

Si vous voulez, je peux :
- ajouter un script `backend/README_QUICKSTART.bat` pour automatiser venv + install + run sur Windows ;
- écrire une petite suite de tests pytest (smoke) pour `helpers/produits.py` ;
- commencer une migration pour autoriser `prix_unitaire` NULL si vous préférez.

Dites ce que vous voulez que j'automatise ensuite.
