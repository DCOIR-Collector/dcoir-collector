export function runFormatter(source: string, input: unknown) {
  const formatter = new Function("input", source);
  return formatter(input);
}
