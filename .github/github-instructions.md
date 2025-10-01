# Copilot instructions for the ecomarche-dashboard repository

Keep this short, actionable, and specific to this codebase so an AI coding agent can be productive quickly.

1) Big-picture architecture
- Two main parts: `backend/` (Flask + SQLAlchemy API) and `ecomarche-frontend/` (Angular app).
- Backend serves a REST API under `/api/produits/<route>` via `backend/resources/produits.py` and helpers in `backend/helpers/produits.py`.
- Frontend calls backend endpoints at `http://localhost:8000` (see `src/app/services/api.ts`).
- Data model: `backend/model/ecomarche_db.py` defines `Produit` with a `date_peremption` field used to compute "à risque" products and dynamic pricing.

2) Key files to read first
- `backend/app.py` — app registration, API resource registration, DB init.
- `backend/resources/produits.py` — main entrypoint for produit REST routes (create, all, predict (deprecated), pricing).
- `backend/helpers/produits.py` — business logic for CRUD, `predict_demand()` (now disabled) and `calculate_pricing()`.
- `backend/model/pricing_model.py` — pricing logic used by `calculate_pricing()`.
- `ecomarche-frontend/src/app/services/api.ts` — client service; shows exact endpoints and expected request/response shapes.
- `ecomarche-frontend/src/app/dashboard/` — dashboard UI and logic; good place to add UX changes.

3) Developer workflows & commands
- Backend local dev (recommended):
  - Create venv: `python -m venv venv`
  - Activate (cmd.exe): `venv\\Scripts\\activate.bat`
  - Install deps: `pip install -r requirements.txt` or `pip install Flask Flask-Cors Flask-Migrate Flask-RESTful Flask-SQLAlchemy`
  - DB migrations: `flask db init && flask db migrate -m "init" && flask db upgrade`
  - Run API: `python app.py` (app listens on port 8000 by default).
- Frontend local dev:
  - In `ecomarche-frontend/`: `npm install` then `npm start` (runs `ng serve`).
  - Common issue: `.angular/cache` can become locked; remove or rename it before restarting the dev server if you see EBUSY.

4) Project-specific conventions & patterns
- Route dispatching uses a single resource `ProduitsApi` with the route token `route` to switch behaviour (e.g. `/api/produits/create`, `/api/produits/pricing`). Look for `route` string logic rather than separate endpoints.
- Expiry logic central: `date_peremption` is the primary field to determine risk and pricing. Do not rename this field globally without updating both front & back.
- Prediction feature is intentionally disabled: frontend & backend stubs exist. If reintroducing prediction, update both `ecomarche-frontend` API client and `backend/helpers/produits.py`.
- Session persistence for user-created products is handled client-side (the UI can use `sessionStorage` for temporary records).

5) Integration points & external deps
- Backend: Flask (+ extensions), SQLAlchemy, scikit-learn/joblib for saved models (models are under `backend/model/*.joblib`).
- Frontend: Angular (13+), Chart.js used for charts. Styles import Bootstrap via SCSS.

6) Making edits safely (recommended checklist)
- If changing API shapes, update `ecomarche-frontend/src/app/services/api.ts` request/response interfaces first.
- When changing `date_peremption` handling, run a quick migration check: if DB stores ISO strings, ensure both front & back use same serialization.
- To add new backend endpoints, register them in `backend/resources/produits.py` and implement logic in `backend/helpers/produits.py`.

7) Tests & quick smoke checks
- No automated test suite present; use the following manual checks:
  - Backend: run `python app.py` then `curl http://localhost:8000/api/produits/all` to inspect JSON.
  - Frontend: `npm start`, open `http://localhost:4200`, navigate to Dashboard and ensure charts load and CRUD actions call the API.

8) Example patterns to copy
- Pricing POST: request shape is `TarificationRequest { produit_id, jours_avant_peremption }` and response `TarificationResponse` (open `src/app/services/api.ts` for exact fields). Use these interfaces when sending pricing requests.
- Products listing: `GET /api/produits/all` returns a list of `Produit` objects; the frontend expects `date_peremption` as ISO date strings.

9) Troubleshooting hints
- If `ng serve` fails with EBUSY referencing `.angular\\cache`, stop the dev server, delete or rename `.angular\\cache`, then restart.
- If backend import errors appear in your editor (`flask` unresolved), ensure the project's venv is activated in your editor and dependencies installed.

If you want, I can open a PR with these instructions or modify them to include more examples (response/request JSON samples, cURL examples). Tell me which additions you'd like.
