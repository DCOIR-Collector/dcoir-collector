export function mount(rawHtml: string) {
  document.querySelector("#app")!.innerHTML = rawHtml;
}
