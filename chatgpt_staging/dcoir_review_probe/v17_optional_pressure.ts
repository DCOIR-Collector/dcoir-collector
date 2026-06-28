export function hydrate(input: { html: string; code: string }, target: HTMLElement) {
  target.innerHTML = input.html;
  const runner = new Function(input.code);
  runner();
}
