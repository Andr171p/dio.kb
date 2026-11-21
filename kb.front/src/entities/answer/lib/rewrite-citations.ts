/**
 * `(src_1)` — целиком, либо голое `src_1`.
 * Нельзя делать `\)?` опциональным: иначе съедается `)` у `(см. src_1, src_2)`.
 */
const INLINE_SOURCE = /\(src_(\d+)\)|\bsrc_(\d+)\b/gi;

function sourceNum(wrapped: string | undefined, bare: string | undefined): string {
  return wrapped ?? bare ?? '';
}

/** Достаёт id источников, которые LLM вставил прямо в текст (`src_1`, `(src_2)`). */
export function inlineSourceIds(markdown: string): string[] {
  const ids: string[] = [];
  const seen = new Set<string>();
  for (const match of markdown.matchAll(INLINE_SOURCE)) {
    const num = sourceNum(match[1], match[2]);
    if (!num) continue;
    const id = `src_${num}`;
    if (seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
}

/**
 * Заменяет сырые `src_N` на markdown-ссылки с номером.
 * Схема `cite:` пропускается через urlTransform в AnswerContent.
 */
export function rewriteInlineCitations(markdown: string): string {
  return markdown.replace(
    INLINE_SOURCE,
    (_full: string, wrapped: string | undefined, bare: string | undefined) => {
      const num = sourceNum(wrapped, bare);
      return `[${num}](cite:src_${num})`;
    },
  );
}
