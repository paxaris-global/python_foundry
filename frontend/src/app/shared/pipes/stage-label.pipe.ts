import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'stageLabel', standalone: true })
export class StageLabelPipe implements PipeTransform {
  transform(value: string): string {
    return value
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  }
}
