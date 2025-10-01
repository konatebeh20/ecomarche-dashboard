# ecomarche-frontend — ecomarche-dashboard

Frontend Angular pour le projet ecomarche-dashboard. Ce README explique comment démarrer le projet, où modifier l'UI et comment le connecter au backend Flask.

Prérequis

- Node.js 16+ (ou version compatible Angular 13+)
- npm ou yarn
- Backend `http://localhost:8000` en cours d'exécution (par défaut)

Installation et démarrage (dev)

```bash
cd ecomarche-frontend
npm install
npm start    # exécute 'ng serve' généralement sur http://localhost:4200
```

Configuration API

- L'URL du backend est codée par défaut dans `src/app/services/api.ts` (variable `apiUrl`). Changez-la si votre API n'écoute pas sur `http://localhost:8000`.

Points importants et améliorations recommandées

1. Intégration ML
- Le frontend possède désormais des méthodes clientes pour les endpoints ML :
	- `getRisksRecommendations()` -> `/api/risques/recommandations`
	- `predictRiskForProduct(id)` -> `/api/risques/predict/:id`
- Utilisez ces endpoints pour enrichir le tableau "Produits à risque" avec la colonne `model_risk_prob` et des actions recommandées.

2. Modal "Appliquer remise"
- La modal actuelle permet d'appliquer un discount et d'éditer le stock et la date de péremption. Assurez-vous que le formulaire valide `date_peremption` (format ISO) et `stock` (entier >= 0).

3. Affichage des prix
- Le backend est désormais la source de vérité pour `prix_unitaire`. Le frontend masque les prix à 0; préférez montrer "—" ou "N/A" pour indiquer l'absence d'information plutôt que 0 FCFA.

4. Internationalisation / devise
- Remplacez l'étiquette de devise par "FCFA" (déjà pris en compte dans les templates). Pour support multi-devises, externaliser dans un service et utiliser des pipes pour le formatage.

5. Tests unitaires
- Le frontend inclut des specs Jasmine/Karma de base. Ajoutez des tests d'intégration pour vérifier la consommation des nouveaux endpoints ML et la logique de la modal promotion.

6. Performance & UX
- Charger les recommandations ML asynchrones (Lazy) et montrer un placeholder pendant le calcul.
- Eviter de bloquer le rendu initial sur la disponibilité du modèle.

7. Sécurité
- Valider côté backend toutes les requêtes modifiant prix/stock (auth non implémentée dans ce dépôt). Même si l'UI masque certaines actions, le backend doit absolument vérifier et autoriser.

8. Déploiement
- Frontend build : `npm run build` puis servir `dist/` avec un serveur statique (nginx) ou via Docker.

Actions proposées (je peux implémenter)

- Ajouter un composant UI qui affiche les recommandations ML (avec tri et filtres).
- Ajouter des tests frontend consommant le backend via des mocks.
- Préparer un script de build & dockerisation pour le frontend.

Dites-moi quelle amélioration vous souhaitez que j'implémente en priorité.
