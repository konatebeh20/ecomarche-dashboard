"""
Modèles de données pour l'application EcoMarché
"""
from datetime import datetime, timedelta
from config.db import db
from config.constant import CATEGORIES, STATUT_EN_STOCK

class Produit(db.Model):
    """Modèle pour les produits"""
    __tablename__ = "produits"

    id = db.Column(db.Integer, primary_key=True, index=True)
    nom = db.Column(db.String(100), index=True)
    categorie_id = db.Column(db.Integer)
    stock = db.Column(db.Integer, default=0)
    prix_unitaire = db.Column(db.Float)
    fournisseur = db.Column(db.String(100))
    date_peremption = db.Column(db.Date)
    
    @property
    def categorie(self):
        """Retourne le nom de la catégorie"""
        return CATEGORIES.get(self.categorie_id, "Autre")
    
    @property
    def jours_restants(self):
        """Calcule le nombre de jours avant péremption"""
        if not self.date_peremption:
            return None
        delta = self.date_peremption - datetime.now().date()
        return delta.days
    
    @property
    def statut(self):
        """Détermine le statut du produit"""
        if self.stock <= 0:
            return "Rupture de stock"
        elif self.stock < 5:
            return "Stock bas"
        else:
            return STATUT_EN_STOCK
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            "id": self.id,
            "nom": self.nom,
            "categorie_id": self.categorie_id,
            "categorie": self.categorie,
            "stock": self.stock,
            "prix_unitaire": self.prix_unitaire,
            "fournisseur": self.fournisseur,
            "date_peremption": self.date_peremption.isoformat() if self.date_peremption else None,
            "jours_restants": self.jours_restants,
            "statut": self.statut,
            # include current active promotion if any
            "promotion": self.get_active_promotion()
        }

    def get_active_promotion(self):
        """Return the active promotion for this product if one exists (dict) or None."""
        try:
            # Import here to avoid circular import issues when models are initialized
            Promotion = globals().get('Promotion')
            if not Promotion:
                return None
            prom = Promotion.query.filter_by(produit_id=self.id, active=True).order_by(Promotion.created_at.desc()).first()
            if not prom:
                return None
            return {
                'id': prom.id,
                'discount_percent': prom.discount_percent,
                'start_date': prom.start_date.isoformat() if prom.start_date else None,
                'end_date': prom.end_date.isoformat() if prom.end_date else None,
                'active': prom.active
            }
        except Exception:
            return None


class Promotion(db.Model):
    """Simple model to represent an applied promotion on a product.

    We store promotions instead of overwriting the base price so promotions are auditable
    and reversible. For a production system we'd add more fields and constraints.
    """
    __tablename__ = 'promotions'

    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, index=True, nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'produit_id': self.produit_id,
            'discount_percent': self.discount_percent,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Fonction pour générer des données de test
def generer_donnees_test():
    """Génère des données de test pour la base de données"""
    
    # Vérifier si des données existent déjà
    if Produit.query.count() > 0:
        return
    
    # Créer des produits de test
    produits = [
        Produit(
            nom="Lait entier",
            categorie_id=1,
            stock=20,
            prix_unitaire=1.2,
            fournisseur="Ferme Duval",
            date_peremption=datetime.now().date() + timedelta(days=10)
        ),
        Produit(
            nom="Pain complet",
            categorie_id=2,
            stock=15,
            prix_unitaire=2.5,
            fournisseur="Boulangerie Martin",
            date_peremption=datetime.now().date() + timedelta(days=3)
        ),
        Produit(
            nom="Pommes Golden",
            categorie_id=3,
            stock=50,
            prix_unitaire=0.8,
            fournisseur="Vergers Bio",
            date_peremption=datetime.now().date() + timedelta(days=15)
        ),
        Produit(
            nom="Carottes",
            categorie_id=4,
            stock=30,
            prix_unitaire=1.0,
            fournisseur="Ferme Bio Locale",
            date_peremption=datetime.now().date() + timedelta(days=20)
        ),
        Produit(
            nom="Yaourt nature",
            categorie_id=1,
            stock=8,
            prix_unitaire=0.9,
            fournisseur="Ferme Duval",
            date_peremption=datetime.now().date() + timedelta(days=5)
        ),
        Produit(
            nom="Baguette tradition",
            categorie_id=2,
            stock=3,
            prix_unitaire=1.2,
            fournisseur="Boulangerie Martin",
            date_peremption=datetime.now().date() + timedelta(days=1)
        ),
        Produit(
            nom="Bananes",
            categorie_id=3,
            stock=25,
            prix_unitaire=1.5,
            fournisseur="Importation Équitable",
            date_peremption=datetime.now().date() + timedelta(days=7)
        ),
        Produit(
            nom="Tomates",
            categorie_id=4,
            stock=0,
            prix_unitaire=2.0,
            fournisseur="Ferme Bio Locale",
            date_peremption=datetime.now().date() + timedelta(days=5)
        ),
        Produit(
            nom="Courgettes",
            categorie_id=4,
            stock=15,
            prix_unitaire=1.8,
            fournisseur="Ferme des Légumes",
            date_peremption=datetime.now().date() + timedelta(days=7)
        ),
        # Produit(
        #     nom="Steak haché",
        #     categorie_id=5,
        #     stock=10,
        #     prix_unitaire=4.5,
        #     fournisseur="Boucherie Centrale",
        #     date_peremption=datetime.now().date() + timedelta(days=5)
        # ),
        Produit(
            nom="Saumon frais",
            categorie_id=6,
            stock=8,
            prix_unitaire=12.0,
            fournisseur="Pêcherie Maritime",
            date_peremption=datetime.now().date() + timedelta(days=2)
        ),
        Produit(
            nom="Pâtes complètes",
            categorie_id=7,
            stock=40,
            prix_unitaire=1.5,
            fournisseur="Épicerie Italienne",
            date_peremption=datetime.now().date() + timedelta(days=180)
        ),
        Produit(
            nom="Jus d'orange",
            categorie_id=8,
            stock=25,
            prix_unitaire=2.0,
            fournisseur="Fruits Pressés",
            date_peremption=datetime.now().date() + timedelta(days=20)
        ),
        Produit(
            nom="Pizza surgelée",
            categorie_id=9,
            stock=15,
            prix_unitaire=3.5,
            fournisseur="Surgelés Express",
            date_peremption=datetime.now().date() + timedelta(days=90)
        ),
        Produit(
            nom="Savon bio",
            categorie_id=10,
            stock=30,
            prix_unitaire=3.0,
            fournisseur="Cosmétiques Naturels",
            date_peremption=datetime.now().date() + timedelta(days=365)
        )
    ]
    
    # Ajouter les produits à la base de données
    for produit in produits:
        db.session.add(produit)
    
    db.session.commit()
    print("Données de test générées avec succès")