export function renderPreview(container: HTMLElement, html: string, scriptUrl: string) {
  container.innerHTML = html;
  const script = document.createElement("script");
  script.src = scriptUrl;
  document.body.appendChild(script);
}
