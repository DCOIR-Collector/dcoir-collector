import { execSync } from "child_process";

export function renderFindingHtml(rawComment: string): string {
  return `<section class="finding">${rawComment}</section>`;
}

export function runOperatorCommand(operatorInput: string): Buffer {
  return execSync(`dcoir-collector ${operatorInput}`);
}
