#!/bin/bash
# Quick fix script for Angular NgModule duplication error
# Run this in your hotel-management-system/frontend directory

echo "Fixing app.module.ts..."

cat > src/app/app.module.ts << 'EOF'
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { CustomersModule } from './features/customers/customers.module';

@NgModule({
  declarations: [AppComponent],
  imports: [BrowserModule, HttpClientModule, AppRoutingModule, CustomersModule],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule {}
EOF

echo "Checking customers.module.ts..."
if grep -q "FormsModule" src/app/features/customers/customers.module.ts; then
    echo "✓ customers.module.ts already has FormsModule"
else
    echo "Adding FormsModule to customers.module.ts..."
    cat > src/app/features/customers/customers.module.ts << 'EOF'
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { CustomerListComponent } from './components/customer-list.component';

@NgModule({
  declarations: [CustomerListComponent],
  imports: [CommonModule, HttpClientModule, FormsModule],
  exports: [CustomerListComponent]
})
export class CustomersModule {}
EOF
fi

echo ""
echo "✓ Angular module fix complete!"
echo ""
echo "Now rebuild:"
echo "  docker compose down"
echo "  docker compose up -d --build"
