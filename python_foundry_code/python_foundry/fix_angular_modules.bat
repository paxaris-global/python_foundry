@echo off
REM Fix Angular NgModule duplication error on Windows
REM Run this in: C:\Users\Admin\Downloads\download_ai_project\hotel-management-system

echo Fixing app.module.ts...

(
echo import { NgModule } from '@angular/core';
echo import { BrowserModule } from '@angular/platform-browser';
echo import { HttpClientModule } from '@angular/common/http';
echo.
echo import { AppRoutingModule } from './app-routing.module';
echo import { AppComponent } from './app.component';
echo import { CustomersModule } from './features/customers/customers.module';
echo.
echo @NgModule^({
echo   declarations: [AppComponent],
echo   imports: [BrowserModule, HttpClientModule, AppRoutingModule, CustomersModule],
echo   providers: [],
echo   bootstrap: [AppComponent]
echo }^)
echo export class AppModule {}
) > src\app\app.module.ts

echo Checking customers.module.ts...
findstr /M "FormsModule" src\app\features\customers\customers.module.ts
if errorlevel 1 (
    echo Adding FormsModule to customers.module.ts...
    
    (
    echo import { NgModule } from '@angular/core';
    echo import { CommonModule } from '@angular/common';
    echo import { FormsModule } from '@angular/forms';
    echo import { HttpClientModule } from '@angular/common/http';
    echo import { CustomerListComponent } from './components/customer-list.component';
    echo.
    echo @NgModule^({
    echo   declarations: [CustomerListComponent],
    echo   imports: [CommonModule, HttpClientModule, FormsModule],
    echo   exports: [CustomerListComponent]
    echo }^)
    echo export class CustomersModule {}
    ) > src\app\features\customers\customers.module.ts
) else (
    echo ✓ customers.module.ts already has FormsModule
)

echo.
echo ✓ Angular module fix complete!
echo.
echo Now rebuild:
echo   docker compose down
echo   docker compose up -d --build
echo.
pause
