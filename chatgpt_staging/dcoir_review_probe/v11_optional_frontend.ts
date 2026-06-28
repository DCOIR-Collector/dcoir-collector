export function renderPreview(target: HTMLElement, html: string, expression: string): void {
  target.innerHTML = html;
  const preview = new Function("return " + expression);
  target.setAttribute("data-preview", String(preview()));
}
