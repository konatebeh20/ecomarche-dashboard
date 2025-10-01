import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Produit, TarificationResponse } from '../services/api';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.scss']
})
export class DashboardComponent implements OnInit {
  produits: Produit[] = [];
  produitsArisque: any[] = [];
  wasteStats: { avgDaysRemaining: number, buckets: {label: string, count: number}[] } = { avgDaysRemaining: 0, buckets: [] };
  // Sales charts data
  salesDaily: any[] = [];
  topProducts: any[] = [];
  // KPIs
  kpiOverview: any = null;
  seasonality: any = null;
  popularBySeason: any = null;
  salesByAge: any = null;
  // Recommendations
  recommendations: any[] = [];
  // Modal state for applying recommendations
  confirmModalVisible: boolean = false;
  pendingRecommendation: any = null;
  // UI state for apply action
  applyingRecommendation: boolean = false;
  toastMessage: string | null = null;
  toastTimeout: any = null;
  // Discount controls
  discountMode: 'auto' | 'manual' = 'auto';
  autoDiscount: number = 0;
  manualDiscount: number | null = null;

  // Modal editable fields for quick product fixes
  modalEditedStock: number | null = null;
  modalEditedDate: string | null = null;

  // Helper methods used by template (avoid strictTemplate 'unknown' errors)
  getPopularList(season: string): any[] {
    try {
      if (!this.popularBySeason || !this.popularBySeason.popular_by_season) return [];
      const arr = this.popularBySeason.popular_by_season[season];
      return Array.isArray(arr) ? arr.slice(0,5) : [];
    } catch(e) { return []; }
  }

  getSalesByAgeList(): any[] {
    try {
      if (!this.salesByAge || !this.salesByAge.overall_by_age) return [];
      return Array.isArray(this.salesByAge.overall_by_age) ? this.salesByAge.overall_by_age : [];
    } catch(e) { return []; }
  }
  newProduit: Partial<Produit> = {
    nom: '',
    categorie_id: undefined,
    stock: 0,
    prix_unitaire: 0,
    date_peremption: ''
  };

  // (Prédiction de la demande supprimée)

  // Tarification dynamique
  selectedPricingProductId: number | null = null;
  daysBeforeExpiry: number = 5;
  pricingData: TarificationResponse | null = null;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadProduits();
    this.loadSalesData();
    this.loadKpis();
    this.loadWasteRecommendations();
  }

  loadWasteRecommendations(): void {
    this.apiService.getWasteRecommendations().subscribe({
      next: (r) => {
        this.recommendations = Array.isArray(r) ? r : [];
      },
      error: (err) => { console.error('Erreur chargement recommendations', err); this.recommendations = []; }
    });
  }

  openRecommendationModal(rec: any): void {
    this.pendingRecommendation = rec;
    // compute suggested discount based on jours_restants
    const days = (rec && typeof rec.jours_restants === 'number') ? rec.jours_restants : 9999;
    this.autoDiscount = this.computeAutoDiscount(days);
    // default manualDiscount to suggested value
    this.manualDiscount = this.autoDiscount;
    this.discountMode = 'auto';
    // pre-fill modal editable fields from the produit (if available)
    const produit = this.produits.find(p => p.id === rec.product_id || p.id === rec.id);
    this.modalEditedStock = produit && typeof produit.stock === 'number' ? produit.stock : null;
    this.modalEditedDate = produit && produit.date_peremption ? (produit.date_peremption as string).split('T')[0] : null;
    this.confirmModalVisible = true;
  }

  cancelRecommendation(): void {
    this.pendingRecommendation = null;
    this.confirmModalVisible = false;
  }

  confirmApplyRecommendation(): void {
    if (!this.pendingRecommendation) return;
    // reuse existing flow
    // choose discount based on mode
    const discountToApply = (this.discountMode === 'manual' && this.manualDiscount !== null) ? this.manualDiscount : this.autoDiscount || this.pendingRecommendation.recommended_discount || 0;
    // attach the chosen discount to the pendingRecommendation so applyRecommendedDiscount can read it
    this.pendingRecommendation.recommended_discount = discountToApply;
    // If product edits were made, send update to backend first
    const produit = this.produits.find(p => p.id === this.pendingRecommendation.product_id || p.id === this.pendingRecommendation.id);
    const updatePayload: any = {};
    if (this.modalEditedStock !== null && produit && this.modalEditedStock !== produit.stock) updatePayload.stock = this.modalEditedStock;
    if (this.modalEditedDate !== null && produit && this.modalEditedDate !== (produit.date_peremption || '').split('T')[0]) updatePayload.date_peremption = this.modalEditedDate;

    const proceedWithApply = () => {
      this.applyRecommendedDiscount(this.pendingRecommendation);
      this.cancelRecommendation();
    };

    if (produit && Object.keys(updatePayload).length > 0) {
      this.applyingRecommendation = true; // keep UI disabled while we update
      this.apiService.updateProduit(produit.id, updatePayload).subscribe({
        next: (res) => {
          // merge local produit changes to keep UI consistent
          if (res && res.stock !== undefined) produit.stock = res.stock;
          if (res && res.date_peremption) produit.date_peremption = res.date_peremption;
          proceedWithApply();
        },
        error: (err) => {
          console.error('Erreur update produit depuis modal', err);
          // still proceed with applying discount if update failed optionally
          proceedWithApply();
        },
        complete: () => { this.applyingRecommendation = false; }
      });
    } else {
      proceedWithApply();
    }
  }

  private computeAutoDiscount(days: number): number {
    // Heuristic buckets: >60 days: 0, 30-60: 10%, 14-30: 20%, 7-14: 30%, 3-7: 40%, <=3: 50%
    if (days > 60) return 0;
    if (days > 30) return 10;
    if (days > 14) return 20;
    if (days > 7) return 30;
    if (days > 3) return 40;
    return 50;
  }

  loadKpis(): void {
    this.apiService.getKpiOverview().subscribe({
      next: (k) => {
        this.kpiOverview = k;
      },
      error: (err) => {
        console.error('Erreur chargement KPIs', err);
        this.kpiOverview = null;
      }
    });

    this.apiService.getSalesSeasonality().subscribe({
      next: (s) => {
        this.seasonality = s;
        setTimeout(()=> this.renderSeasonalityChart(), 200);
      },
      error: (err) => {
        console.error('Erreur chargement seasonality', err);
        this.seasonality = null;
      }
    });

    this.apiService.getPopularBySeason().subscribe({
      next: (p) => { this.popularBySeason = p; },
      error: (err) => { console.error('Erreur popular by season', err); this.popularBySeason = null; }
    });

    this.apiService.getSalesByAgeGroups().subscribe({
      next: (a) => { this.salesByAge = a; },
      error: (err) => { console.error('Erreur sales by age', err); this.salesByAge = null; }
    });
  }

  loadSalesData(): void {
    // fetch daily sales and top products
    this.apiService.getSalesSummary().subscribe({
      next: (daily) => {
        this.salesDaily = daily || [];
        setTimeout(() => this.renderSalesChart(), 200);
      },
      error: (err) => {
        console.error('Erreur chargement sales summary', err);
        this.salesDaily = [];
      }
    });

    this.apiService.getTopProducts().subscribe({
      next: (top) => {
        this.topProducts = top || [];
        setTimeout(() => this.renderTopProductsChart(), 200);
      },
      error: (err) => {
        console.error('Erreur chargement top products', err);
        this.topProducts = [];
      }
    });
  }

  loadProduits(): void {
    this.apiService.getProduits().subscribe({
      next: (data) => {
        // Ensure we always have an array (backend may wrap the response)
        this.produits = Array.isArray(data) ? data : (data && Array.isArray((data as any).produits) ? (data as any).produits : []);
        // Use backend as source-of-truth: remove any client-side price overrides and clear createdProduits
        try {
          this.produits = this.produits.map(p => {
            // remove transient 'prix_affiche' if present so UI reads prix_unitaire from backend
            if ((p as any).hasOwnProperty('prix_affiche')) delete (p as any).prix_affiche;
            return p;
          });
          // clear any client-created products cached in sessionStorage to avoid stale duplicates overriding backend
          sessionStorage.removeItem('createdProduits');
        } catch(e) {
          // ignore session storage errors
        }
        this.calculateExpiryDays();
        this.computeWasteStats();
        setTimeout(() => this.renderWasteChart(), 200);
      },
      error: (error) => {
        console.error('Erreur lors du chargement des produits', error);
        // Données de test en cas d'erreur
        this.produits = this.getMockProduits();
        this.calculateExpiryDays();
      }
    });
  }

  calculateExpiryDays(): void {
    const today = new Date();

    this.produitsArisque = this.produits
      .map(produit => {
  const expiryDate = produit.date_peremption ? new Date(produit.date_peremption as string) : null;
  const diffTime = expiryDate ? (expiryDate.getTime() - today.getTime()) : Infinity;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        return {
          ...produit,
          jours_restants: diffDays
        };
      })
      .filter(produit => produit.jours_restants <= 14)
      .sort((a, b) => a.jours_restants - b.jours_restants);
    // also update waste stats
    this.computeWasteStats();
  }

  private computeWasteStats(): void {
    if (!this.produits || this.produits.length === 0) {
      this.wasteStats = { avgDaysRemaining: 0, buckets: [] };
      return;
    }

    const days = this.produits.map(p => {
      const d = p.date_peremption ? Math.ceil((new Date(p.date_peremption).getTime() - new Date().getTime()) / (1000*60*60*24)) : 9999;
      return isNaN(d) ? 9999 : d;
    });

    const avg = Math.round(days.reduce((a,b)=>a+b,0)/days.length);

    const buckets = [
      { label: '>7j', count: days.filter(d=>d>7).length },
      { label: '3-7j', count: days.filter(d=>d>3 && d<=7).length },
      { label: '≤3j', count: days.filter(d=>d<=3).length }
    ];

    this.wasteStats = { avgDaysRemaining: avg, buckets };
  }

  private renderWasteChart(): void {
    // Guard for server-side rendering / build where `document` is not defined
    if (typeof document === 'undefined') return;
    const canvas = document.getElementById('wasteChart') as HTMLCanvasElement | null;
    const ctx = canvas ? canvas.getContext('2d') : null;
    if (!ctx) return;

    const labels = this.wasteStats.buckets.map(b=>b.label);
    const data = this.wasteStats.buckets.map(b=>b.count);

    // destroy existing chart if any
    try {
      // @ts-ignore
      if ((window as any).wasteChartInstance) {
        // @ts-ignore
        (window as any).wasteChartInstance.destroy();
      }
    } catch(e) {}

    // @ts-ignore
    (window as any).wasteChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{ data, backgroundColor: ['#28a745','#ffc107','#dc3545'] }]
      },
      options: { responsive: true }
    });
  }

  private renderSalesChart(): void {
    if (typeof document === 'undefined') return;
    const canvas = document.getElementById('salesChart') as HTMLCanvasElement | null;
    const ctx = canvas ? canvas.getContext('2d') : null;
    if (!ctx) return;

    const labels = this.salesDaily.map(s => {
      if (!s) return '';
      const d = s.Date || s.date || s.date_str || s.Date_str;
      try {
        const dt = new Date(d);
        if (!isNaN(dt.getTime())) return dt.toISOString().split('T')[0];
      } catch(e) {}
      return (typeof d === 'string') ? d : '';
    });
    const data = this.salesDaily.map(s => s.Daily_Sales || s.daily_sales || s.value || 0);

    try { if ((window as any).salesChartInstance) (window as any).salesChartInstance.destroy(); } catch(e) {}
    (window as any).salesChartInstance = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [{ label: 'Ventes journalières', data, borderColor: '#007bff', backgroundColor: 'rgba(0,123,255,0.1)' }] },
      options: { responsive: true }
    });
  }

  private renderTopProductsChart(): void {
    if (typeof document === 'undefined') return;
    const canvas = document.getElementById('topProductsChart') as HTMLCanvasElement | null;
    const ctx = canvas ? canvas.getContext('2d') : null;
    if (!ctx) return;

    const labels = this.topProducts.map(p => p.Product_Name || p.product_name || p.name || '');
    const data = this.topProducts.map(p => p.Daily_Sales || p.daily_sales || p.Total || p.sales || 0);

    try { if ((window as any).topProductsChartInstance) (window as any).topProductsChartInstance.destroy(); } catch(e) {}
    (window as any).topProductsChartInstance = new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: [{ label: 'Ventes totales', data, backgroundColor: labels.map((_,i)=>['#007bff','#28a745','#ffc107','#dc3545'][i % 4]) }] },
      options: { responsive: true }
    });
  }

  private renderSeasonalityChart(): void {
    if (typeof document === 'undefined') return;
    const canvas = document.getElementById('seasonalityChart') as HTMLCanvasElement | null;
    const ctx = canvas ? canvas.getContext('2d') : null;
    if (!ctx) return;

    const months = (this.seasonality && this.seasonality.seasonality_by_month) ? this.seasonality.seasonality_by_month : [];
    const labels = months.map((m: any) => {
      try { return new Date(m.Month).toISOString().slice(0,10); } catch(e) { return m.Month || m.month || String(m.month); }
    });
    const data = months.map((m: any) => m.Daily_Sales || m.daily_sales || m.value || 0);

    try { if ((window as any).seasonalityChartInstance) (window as any).seasonalityChartInstance.destroy(); } catch(e) {}
    (window as any).seasonalityChartInstance = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [{ label: 'Ventes par mois', data, borderColor: '#28a745', backgroundColor: 'rgba(40,167,69,0.1)' }] },
      options: { responsive: true }
    });
  }

  // Product creation + sessionStorage
  createProduitLocal(produit: Partial<Produit>): void {
    // save to backend and to sessionStorage for quick access
    // map frontend-friendly fields to backend payload
    const payload: any = {
      nom: produit.nom,
      categorie_id: produit.categorie_id || null,
      stock: produit.stock || 0,
      prix_unitaire: produit.prix_unitaire || 0,
      fournisseur: (produit as any).fournisseur || 'Inconnu',
      date_peremption: produit.date_peremption || null
    };

    this.apiService.createProduit(payload).subscribe({
      next: (saved) => {
        // add to local list and recalc
        if (!this.produits) this.produits = [];
        this.produits.push(saved as Produit);
        this.calculateExpiryDays();
        this.computeWasteStats();
        this.renderWasteChart();
        // persist a record in sessionStorage
        const m = sessionStorage.getItem('createdProduits') || '[]';
        const arr = JSON.parse(m);
        arr.push(saved);
        sessionStorage.setItem('createdProduits', JSON.stringify(arr));
        // refresh recommendations so the new product is evaluated
        this.loadWasteRecommendations();
      },
      error: (err) => {
        console.error('Erreur création produit', err);
      }
    });
  }

  resetNewProduit(): void {
    this.newProduit = { nom: '', categorie_id: undefined, stock: 0, prix_unitaire: 0, date_peremption: '' };
  }

  predictDemand(): void {
    // Méthode de prédiction supprimée - fonctionnalité désactivée
  }


  calculatePricing(): void {
    if (!this.selectedPricingProductId) return;

    const product = this.produits.find(p => p.id === this.selectedPricingProductId);
    // compute an expiry date based on daysBeforeExpiry (backend expects a date)
    const expiry = new Date();
    expiry.setDate(expiry.getDate() + this.daysBeforeExpiry);
    const date_peremption = expiry.toISOString().split('T')[0];

    const request: any = {
      product_id: this.selectedPricingProductId,
      date_peremption,
      stock: product?.stock || 0,
      prix_original: product?.prix_unitaire || 0,
      categorie_id: product?.categorie_id || null
    };

    this.apiService.calculatePricing(request).subscribe({
      next: (data: any) => {
        // Backend may return different key names; normalize into TarificationResponse-like shape
        this.pricingData = {
          produit_id: data.produit_id || data.identifiant_produit || data.produit_id || request.product_id,
          prix_original: data.prix_original || data.prix_original || request.prix_original,
          prix_recommande: data.prix_recommande ?? data.prix_reduit ?? null,
          pourcentage_reduction: data.pourcentage_reduction ?? data.pourcentage_reduction ?? null,
          date_peremption: data.date_peremption || request.date_peremption || date_peremption,
          jours_restants: data.jours_restants ?? data.jours_avant_peremption ?? data.jours_avant_peremption ?? this.daysBeforeExpiry
        } as any;
      },
      error: (error) => {
        console.error('Erreur lors du calcul de la tarification', error);
        // Données de test en cas d'erreur
        this.pricingData = this.getMockPricing(this.selectedPricingProductId!, this.daysBeforeExpiry);
      }
    });
  }

  calculatePricingForProduct(productId: number): void {
    this.selectedPricingProductId = productId;
    this.daysBeforeExpiry = 5;
    this.calculatePricing();
  }

  // Apply a simulated discount action (updates pricingData using local heuristic)
  applyRecommendedDiscount(rec: any): void {
    // Apply the recommended discount via backend and refresh local product + recommendations
    const product = this.produits.find(p => p.id === rec.product_id);
    if (!product) return;
    const discount = rec.recommended_discount || 0;
    // optimistic UI: mark as applying and show temporary badge on product
    this.applyingRecommendation = true;
    // Keep original price in case of rollback
    const originalPrice = (product as any).prix_unitaire;
    try {
      // temporarily show a visual reduction locally
      (product as any).prix_affiche = parseFloat((originalPrice * (1 - discount/100)).toFixed(2));
    } catch(e) {}

    // update the matching recommendation row optimistically
    const recIndex = this.recommendations.indexOf(rec);
    if (recIndex !== -1) {
      const newAction = this.formatActionForDiscount(discount);
      // update the existing object so template bindings update in-place
      this.recommendations[recIndex].recommended_discount = discount;
      this.recommendations[recIndex].recommended_action = newAction;
    }

    this.apiService.applyDiscount(product.id, discount).subscribe({
      next: (res) => {
        // final refresh so server-side promotion is reflected
        this.loadProduits();
        // reload recommendations and ensure they reflect the applied discount
        this.loadWasteRecommendations();
        this.showToast(`Remise de ${discount}% appliquée à ${product.nom}`);
      },
      error: (err) => {
        console.error('Erreur applying discount', err);
        // rollback optimistic change
        (product as any).prix_affiche = originalPrice;
        // revert recommendation row (reload to be safe)
        this.loadWasteRecommendations();
        this.showToast(`Échec application remise pour ${product.nom}`);
      },
      complete: () => {
        this.applyingRecommendation = false;
      }
    });
  }

  private formatActionForDiscount(discount: number): string {
    if (!discount || discount <= 0) return 'Surveiller le stock (0%)';
    if (discount >= 50) return `Remise immédiate importante (${discount}%)`;
    if (discount >= 40) return `Remise immédiate importante (${discount}%)`;
    if (discount >= 30) return `Remise ${discount}% (${discount}%)`;
    if (discount >= 20) return `Promotion multi-achat (${discount}%)`;
    if (discount >= 10) return `Petite promotion (${discount}%)`;
    return `Remise ${discount}% (${discount}%)`;
  }

  private showToast(message: string, ms: number = 3500) {
    this.toastMessage = message;
    if (this.toastTimeout) clearTimeout(this.toastTimeout);
    this.toastTimeout = setTimeout(() => { this.toastMessage = null; this.toastTimeout = null; }, ms);
  }

  resetPricing(): void {
    this.pricingData = null;
    this.selectedPricingProductId = null;
  }

  getProductName(productId: number): string {
    const product = this.produits.find(p => p.id === productId);
    return product ? product.nom : 'Produit inconnu';
  }

  // Méthodes pour générer des données de test
  private getMockProduits(): Produit[] {
    return [
      {
        id: 1,
        nom: 'Yaourt Nature',
        categorie_id: 1,
        fournisseur: 'Laiterie Alpes',
        stock: 120,
    // legacy reordering fields removed from mock data
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
  categorie_id: 2,
  fournisseur: 'Boulangerie Martin',
  stock: 45,
    // legacy reordering fields removed from mock data
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
  categorie_id: 3,
  fournisseur: 'Vergers Bio',
  stock: 80,
    // legacy reordering fields removed from mock data
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
  // id: 4,
  // nom: 'Steak haché',
  // categorie_id: 5,
  // fournisseur: 'Boucherie Centrale',
  // stock: 30,
  //   // legacy reordering fields removed from mock data
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
  categorie_id: 1,
  fournisseur: 'Laiterie Alpes',
  stock: 65,
    // legacy reordering fields removed from mock data
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

  // getMockPrediction removed with prediction feature

  private getMockPricing(productId: number, daysBeforeExpiry: number): TarificationResponse {
    const product = this.produits.find(p => p.id === productId);
    const originalPrice = (product && typeof product.prix_unitaire === 'number') ? product.prix_unitaire : 2.99;

    // Calcul de la réduction en fonction des jours avant péremption
    let reductionPercentage = 0;
    if (daysBeforeExpiry <= 1) {
      reductionPercentage = 50;
    } else if (daysBeforeExpiry <= 3) {
      reductionPercentage = 30;
    } else if (daysBeforeExpiry <= 5) {
      reductionPercentage = 15;
    } else if (daysBeforeExpiry <= 7) {
      reductionPercentage = 10;
    } else {
      reductionPercentage = 5;
    }

    const recommendedPrice = originalPrice * (1 - reductionPercentage / 100);

    // Date de péremption calculée
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + daysBeforeExpiry);

    return {
      produit_id: productId,
      prix_original: originalPrice,
      prix_recommande: parseFloat(recommendedPrice.toFixed(2)),
      pourcentage_reduction: reductionPercentage,
      date_peremption: expiryDate.toISOString().split('T')[0],
      jours_restants: daysBeforeExpiry
    };
  }
}
