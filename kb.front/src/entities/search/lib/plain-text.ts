/** Markdown-фрагмент → короткий текст для сниппета (без разметки, ссылок и картинок). */
export function markdownToSnippet(markdown: string, maxLength = 240): string {
  const text = markdown
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/!\[[^\]]*]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)]\([^)]*\)/g, '$1')
    // Строка-разделитель таблицы: | --- | :---: |
    .replace(/^\s*\|?(\s*:?-{3,}:?\s*\|)+\s*:?-*:?\s*$/gm, ' ')
    .replace(/^\s{0,3}(#{1,6}|>|[-*+]|\d+\.)\s+/gm, '')
    // Отметки чеклиста
    .replace(/^\s*\[[ xX]]\s+/gm, '')
    .replace(/\|/g, ' ')
    .replace(/\*\*|__|~~|`/g, '')
    // Одиночные * и _ — только как обрамление, подчёркивания внутри слов (AUTH_FAILED) сохраняем
    .replace(/(^|[\s(])[*_](?=\S)/g, '$1')
    .replace(/(\S)[*_](?=[\s).,!?:;]|$)/g, '$1')
    .replace(/\s+/g, ' ')
    .trim();

  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text;
}
