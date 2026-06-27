export function Preview({ html }: { html: string }) {
  return <section dangerouslySetInnerHTML={{ __html: html }} />;
}
