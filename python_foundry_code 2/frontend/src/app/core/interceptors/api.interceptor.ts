import { HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

export const apiInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req).pipe(
    catchError((error) => {
      const message =
        error.error?.detail ?? error.error?.message ?? error.statusText ?? 'Unknown error';
      console.error(`[API ${req.method} ${req.url}]`, message);
      return throwError(() => new Error(message));
    })
  );
};
