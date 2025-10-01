import json
import urllib.request

url = 'http://127.0.0.1:8000/api/produits/create'
product = {
    "nom": "Produit_Test_Created_By_Script",
    "categorie_id": 1,
    "stock": 7,
    "prix_unitaire": 3.5,
    "fournisseur": "ScriptFournisseur",
    "date_peremption": "2025-10-15"
}

data = json.dumps(product).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=10) as resp:
    print('HTTP', resp.getcode())
    body = resp.read().decode('utf-8')
    print(body)
