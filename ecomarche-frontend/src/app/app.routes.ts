import { Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard';
import { ProduitsComponent } from './produits/produits';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'produits', component: ProduitsComponent },
  { path: '**', redirectTo: '/dashboard' }
];
