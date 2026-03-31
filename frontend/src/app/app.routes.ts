import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadChildren: () =>
      import('@features/generator/generator.routes').then(
        (m) => m.GENERATOR_ROUTES
      ),
  },
  { path: '**', redirectTo: '' },
];
