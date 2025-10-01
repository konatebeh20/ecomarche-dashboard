import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface Produit {
  id: number;
  nom: string;
  categorie_id?: number;
  categorie?: string;
  // legacy compatibility fields (kept optional for backward compatibility)
  fournisseur_id?: number; // legacy numeric id
  // current fields
  stock?: number;
  fournisseur?: string;
  niveau_reapprovisionnement?: number;
  quantite_reapprovisionnement?: number;
  prix_unitaire?: number;
  date_reception?: string;
  date_derniere_commande?: string;
  date_peremption?: string | null;
  emplacement_entrepot?: string;
  volume_ventes?: number;
  taux_rotation_stocks?: number;
  statut?: string;
  jours_restants?: number | null;
}

// Prediction interfaces removed - feature deprecated

export interface TarificationRequest {
  produit_id: number;
  jours_avant_peremption: number;
}

export interface TarificationResponse {
  produit_id: number;
  prix_original: number;
  prix_recommande: number;
  pourcentage_reduction: number;
  date_peremption: string;
  jours_restants: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) { }

  getProduits(): Observable<Produit[]> {
    // Backend returns an object { status: 'success', produits: [...] }
    // Normalize to return the products array so frontend can use it directly.
    return this.http.get<any>(`${this.apiUrl}/api/produits/all`).pipe(
      map(res => {
        if (!res) return [];
        if (Array.isArray(res)) return res as Produit[];
        if (Array.isArray(res.produits)) return res.produits as Produit[];
        // fallback: try to return any array-like field
        for (const key of Object.keys(res)) {
          if (Array.isArray((res as any)[key])) return (res as any)[key] as Produit[];
        }
        return [];
      })
    );
  }

  getProduit(id: number): Observable<Produit> {
    return this.http.get<Produit>(`${this.apiUrl}/api/produits/${id}`);
  }

  // Accept Partial<Produit> because frontend creation form may only provide a subset
  // and backend wraps responses as { status, produit }
  createProduit(produit: Partial<Produit>): Observable<Produit> {
    return this.http.post<any>(`${this.apiUrl}/api/produits/create`, produit).pipe(
      map(res => {
        if (!res) return res;
        if (res.produit) return res.produit as Produit;
        return res as Produit;
      })
    );
  }

  updateProduit(id: number, produit: Partial<Produit>): Observable<Produit> {
    return this.http.patch<Produit>(`${this.apiUrl}/api/produits/${id}`, produit);
  }

  deleteProduit(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/api/produits/${id}`);
  }

  // predictDemand removed - endpoint deprecated

  calculatePricing(request: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/api/produits/pricing`, request);
  }

  // Sales visualization endpoints
  getSalesSummary(): Observable<any[]> {
    return this.http.get<any>(`${this.apiUrl}/api/sales/summary`).pipe(
      map(res => {
        if (!res) return [];
        if (Array.isArray(res)) return res as any[];
        if (Array.isArray(res.daily)) return res.daily as any[];
        if (Array.isArray(res.data)) return res.data as any[];
        return [];
      })
    );
  }

  getTopProducts(): Observable<any[]> {
    return this.http.get<any>(`${this.apiUrl}/api/sales/top_products`).pipe(
      map(res => {
        if (!res) return [];
        if (Array.isArray(res)) return res as any[];
        if (Array.isArray(res.top_products)) return res.top_products as any[];
        if (Array.isArray(res.data)) return res.data as any[];
        return [];
      })
    );
  }

  getKpiOverview(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/api/kpi/overview`).pipe(
      map(res => res || {})
    );
  }

  getSalesSeasonality(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/api/sales/seasonality`).pipe(
      map(res => res || {})
    );
  }

  getPopularBySeason(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/api/sales/popular_by_season`).pipe(map(res => res || {}));
  }

  getSalesByAgeGroups(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/api/sales/by_age_groups`).pipe(map(res => res || {}));
  }

  getWasteRecommendations(): Observable<any[]> {
    return this.http.get<any>(`${this.apiUrl}/api/kpi/waste_recommendations`).pipe(
      map(res => {
        if (!res) return [];
        if (Array.isArray(res)) return res as any[];
        if (Array.isArray(res.recommendations)) return res.recommendations as any[];
        // fallback: some servers return object with keys
        for (const key of Object.keys(res)) {
          if (Array.isArray((res as any)[key])) return (res as any)[key] as any[];
        }
        return [];
      })
    );
  }

  applyDiscount(productId: number, discountPercent: number): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/api/produits/${productId}/apply_discount`, { discount_percent: discountPercent }).pipe(
      map(res => res || {})
    );
  }

  // ML / Risks endpoints
  getRisksRecommendations(): Observable<any[]> {
    return this.http.get<any>(`${this.apiUrl}/api/risques/recommandations`).pipe(
      map(res => {
        if (!res) return [];
        if (Array.isArray(res.recommendations)) return res.recommendations as any[];
        return [];
      })
    );
  }

  predictRiskForProduct(productId: number): Observable<number | null> {
    return this.http.get<any>(`${this.apiUrl}/api/risques/predict/${productId}`).pipe(
      map(res => {
        if (!res) return null;
        if (typeof res.risk_prob === 'number') return res.risk_prob as number;
        if (typeof res.model_risk_prob === 'number') return res.model_risk_prob as number;
        return null;
      })
    );
  }
}
