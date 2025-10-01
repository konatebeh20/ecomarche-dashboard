import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Produit } from '../services/api';

@Component({
  selector: 'app-produits',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './produits.html',
  styleUrls: ['./produits.scss']
})
export class ProduitsComponent implements OnInit {
  produits: Produit[] = [];
  filteredProduits: Produit[] = [];
  searchTerm: string = '';
  categoryFilter: string = '';
  categories: string[] = [];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadProduits();
  }

  loadProduits(): void {
    this.apiService.getProduits().subscribe({
      next: (data) => {
        this.produits = data;
        this.filteredProduits = [...this.produits];
        this.extractCategories();
      },
      error: (error) => {
        console.error('Erreur lors du chargement des produits', error);
        // Données de test en cas d'erreur
        this.produits = this.getMockProduits();
        this.filteredProduits = [...this.produits];
        this.extractCategories();
      }
    });
  }

  extractCategories(): void {
    this.categories = [...new Set(this.produits.map(p => p.categorie || '').filter(c => c !== ''))] as string[];
  }

  applyFilters(): void {
    this.filteredProduits = this.produits.filter(produit => {
      const name = (produit.nom || '').toLowerCase();
      const category = (produit.categorie || '').toLowerCase();
      const matchesSearch = this.searchTerm === '' || name.includes(this.searchTerm.toLowerCase()) || category.includes(this.searchTerm.toLowerCase());

      const matchesCategory = this.categoryFilter === '' ||
        produit.categorie === this.categoryFilter;

      return matchesSearch && matchesCategory;
    });
  }

  resetFilters(): void {
    this.searchTerm = '';
    this.categoryFilter = '';
    this.filteredProduits = [...this.produits];
  }

  calculateDaysUntilExpiry(expiryDate?: string | null): number {
    const today = new Date();
    if (!expiryDate) return 9999;
    const expiry = new Date(expiryDate as string);
    const diffTime = expiry.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  getExpiryClass(expiryDate?: string | null): string {
    if (!expiryDate) return 'text-muted';
    const daysLeft = this.calculateDaysUntilExpiry(expiryDate);
    if (daysLeft <= 3) return 'text-danger';
    if (daysLeft <= 7) return 'text-warning';
    return 'text-success';
  }

  // Méthode pour générer des données de test
  private getMockProduits(): Produit[] {
    return [
      {
        id: 1,
        nom: 'Yaourt Nature',
        categorie: 'Produits laitiers',
  fournisseur_id: 101,
  fournisseur: 'Laiterie Alpes',
  stock: 120,
        prix_unitaire: 1.20,
        date_reception: '2023-09-15',
        date_derniere_commande: '2023-09-10',
        date_peremption: '2023-10-05',
        emplacement_entrepot: 'A1-B3',
        volume_ventes: 25,
        taux_rotation_stocks: 0.8,
        statut: 'En stock'
      },
      {
        id: 2,
        nom: 'Pain de mie',
        categorie: 'Boulangerie',
  fournisseur_id: 102,
  fournisseur: 'Boulangerie Martin',
  stock: 45,
        prix_unitaire: 2.10,
        date_reception: '2023-09-18',
        date_derniere_commande: '2023-09-16',
        date_peremption: '2023-09-28',
        emplacement_entrepot: 'B2-C4',
        volume_ventes: 12,
        taux_rotation_stocks: 0.6,
        statut: 'En stock'
      },
      {
        id: 3,
        nom: 'Pommes Golden',
        categorie: 'Fruits',
  fournisseur_id: 103,
  fournisseur: 'Vergers Bio',
  stock: 80,
        prix_unitaire: 2.50,
        date_reception: '2023-09-20',
        date_derniere_commande: '2023-09-18',
        date_peremption: '2023-10-10',
        emplacement_entrepot: 'D1-E2',
        volume_ventes: 15,
        taux_rotation_stocks: 0.5,
        statut: 'En stock'
      },
  //     {
  //       id: 4,
  //       nom: 'Steak haché',
  //       categorie: 'Viandes',
  // fournisseur_id: 104,
  // fournisseur: 'Boucherie Centrale',
  // stock: 30,
  //       prix_unitaire: 4.80,
  //       date_reception: '2023-09-22',
  //       date_derniere_commande: '2023-09-20',
  //       date_peremption: '2023-09-29',
  //       emplacement_entrepot: 'F3-G1',
  //       volume_ventes: 8,
  //       taux_rotation_stocks: 0.7,
  //       statut: 'En stock'
  //     },
      {
        id: 5,
        nom: 'Lait demi-écrémé',
        categorie: 'Produits laitiers',
  fournisseur_id: 101,
  fournisseur: 'Laiterie Alpes',
  stock: 65,
        prix_unitaire: 1.05,
        date_reception: '2023-09-21',
        date_derniere_commande: '2023-09-19',
        date_peremption: '2023-10-15',
        emplacement_entrepot: 'A2-B1',
        volume_ventes: 18,
        taux_rotation_stocks: 0.9,
        statut: 'En stock'
      }
    ];
  }
}
