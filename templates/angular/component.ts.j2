import { AfterViewInit, Component, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiService, Customer } from '../../../core/services/api.service';

@Component({
  selector: 'app-customer-list',
  templateUrl: './customer-list.component.html',
  styleUrls: ['./customer-list.component.css']
})
export class CustomerListComponent implements OnInit, AfterViewInit {
  customers: Customer[] = [];
  dataSource = new MatTableDataSource<Customer>();
  loading = false;
  showAddForm = false;

  displayedColumns: string[] = ['name', 'email', 'company', 'actions'];

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  // Reactive forms
  addForm: FormGroup;

  selectedCustomer: Customer | null = null;
  isEditMode = false;
  filterValue = '';

  constructor(
    private apiService: ApiService,
    private fb: FormBuilder,
    private snackBar: MatSnackBar
  ) {
    // Initialize reactive forms with more fields
    this.addForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      company: [''],
      phone: [''],
      address: ['']
    });
  }

  ngOnInit(): void {
    this.dataSource.filterPredicate = (data: Customer, filter: string) => {
      const f = filter.trim().toLowerCase();
      return (
        (data.name ?? '').toLowerCase().includes(f) ||
        (data.email ?? '').toLowerCase().includes(f) ||
        (data.company ?? '').toLowerCase().includes(f)
      );
    };
    this.fetchCustomers();
  }

  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  fetchCustomers(): void {
    this.loading = true;
    this.apiService.getCustomers().subscribe({
      next: (customers: Customer[]) => {
        this.customers = customers;
        this.dataSource.data = customers;
        this.loading = false;
      },
      error: (err) => {
        this.showError('Failed to load customers. Please try again.');
        console.error('Error loading customers:', err);
        this.loading = false;
      }
    });
  }

  applyFilter(value: string): void {
    this.filterValue = value;
    this.dataSource.filter = value;
    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  addCustomer(): void {
    if (this.addForm.invalid) {
      this.markFormGroupTouched(this.addForm);
      return;
    }

    this.loading = true;
    const customerData = this.addForm.value;

    this.apiService.createCustomer(customerData).subscribe({
      next: () => {
        this.showSuccess('Customer added successfully!');
        this.addForm.reset();
        this.showAddForm = false;
        this.fetchCustomers();
      },
      error: (err) => {
        this.showError('Failed to add customer. Please try again.');
        console.error('Error adding customer:', err);
        this.loading = false;
      }
    });
  }

  editCustomer(customer: Customer): void {
    this.selectedCustomer = { ...customer };
    this.isEditMode = true;
    this.showAddForm = true;
    this.addForm.patchValue({
      name: customer.name,
      email: customer.email,
      company: customer.company || '',
      phone: customer.phone || '',
      address: customer.address || ''
    });
  }

  updateCustomer(): void {
    if (this.addForm.invalid || !this.selectedCustomer) {
      this.markFormGroupTouched(this.addForm);
      return;
    }

    this.loading = true;
    const customerData = this.addForm.value;

    this.apiService.updateCustomer(this.selectedCustomer.id, customerData).subscribe({
      next: () => {
        this.showSuccess('Customer updated successfully!');
        this.cancelEdit();
        this.fetchCustomers();
      },
      error: (err) => {
        this.showError('Failed to update customer. Please try again.');
        console.error('Error updating customer:', err);
        this.loading = false;
      }
    });
  }

  deleteCustomer(customer: Customer): void {
    if (confirm(`Are you sure you want to delete ${customer.name}?`)) {
      this.loading = true;
      this.apiService.deleteCustomer(customer.id).subscribe({
        next: () => {
          this.showSuccess('Customer deleted successfully!');
          this.fetchCustomers();
        },
        error: (err) => {
          this.showError('Failed to delete customer. Please try again.');
          console.error('Error deleting customer:', err);
          this.loading = false;
        }
      });
    }
  }

  cancelEdit(): void {
    this.selectedCustomer = null;
    this.isEditMode = false;
    this.showAddForm = false;
    this.addForm.reset();
  }

  startAdd(): void {
    this.isEditMode = false;
    this.selectedCustomer = null;
    this.showAddForm = true;
    this.addForm.reset();
  }

  private markFormGroupTouched(formGroup: FormGroup): void {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      control?.markAsTouched();
    });
  }

  private showSuccess(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 3000,
      panelClass: ['success-snackbar']
    });
  }

  private showError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  // Helper method for validation display
  isFieldInvalid(form: FormGroup, fieldName: string): boolean {
    const field = form.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  getFieldErrorMessage(form: FormGroup, fieldName: string): string {
    const field = form.get(fieldName);
    if (!field || !field.errors) return '';

    if (field.errors['required']) {
      return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} is required`;
    }
    if (field.errors['email']) {
      return 'Please enter a valid email address';
    }
    if (field.errors['minlength']) {
      return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} must be at least ${field.errors['minlength'].requiredLength} characters`;
    }
    return 'Invalid value';
  }
}
