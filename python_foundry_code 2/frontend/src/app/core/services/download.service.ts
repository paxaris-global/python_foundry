import { Injectable, inject } from '@angular/core';
import { Observable, tap, map } from 'rxjs';
import { GenerationApiService } from './generation-api.service';

@Injectable({ providedIn: 'root' })
export class DownloadService {
  private readonly api = inject(GenerationApiService);

  /**
   * Downloads the generated project ZIP and triggers a browser save dialog.
   */
  download(projectId: string, fileName: string): Observable<void> {
    return this.api.downloadProject(projectId).pipe(
      tap((blob) => {
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = `${fileName}.zip`;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);
      }),
      map(() => void 0)
    );
  }
}
