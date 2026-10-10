const FENCE = /^(```|~~~)/;
/** `[https://x](https://x)` → `https://x`: так ссылку пишет человек, и так её проще читать в истории */
const SELF_LINK = /\[(https?:\/\/[^\s\]]+)\]\(\1\)/g;

/**
 * Приводит Markdown редактора к стабильному виду: без лишних пустых строк
 * (TipTap добавляет их вокруг таблиц) и с одним переводом строки в конце.
 * Содержимое блоков кода не трогаем.
 */
export function normalizeMarkdown(markdown: string): string {
  const lines = markdown.replace(/\r\n?/g, '\n').split('\n');
  const result: string[] = [];
  let inCode = false;
  let blankRun = 0;

  for (const line of lines) {
    if (FENCE.test(line.trimStart())) inCode = !inCode;

    if (!inCode && line.trim() === '') {
      blankRun += 1;
      if (blankRun > 1) continue;
    } else {
      blankRun = 0;
    }
    // Хвостовые пробелы не трогаем: два пробела в конце строки — перенос строки
    result.push(inCode ? line : line.replace(SELF_LINK, '$1'));
  }

  return `${result.join('\n').trim()}\n`;
}
