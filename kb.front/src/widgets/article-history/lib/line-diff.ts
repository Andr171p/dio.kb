import { diffLines, diffWordsWithSpace } from 'diff';

/** Фрагмент строки; `changed` — слова, которые отличаются от парной строки */
export interface Segment {
  text: string;
  changed: boolean;
}

export type DiffLine =
  | {
      kind: 'added' | 'removed' | 'same';
      segments: Segment[];
      oldNumber: number | null;
      newNumber: number | null;
    }
  | { kind: 'skip'; count: number };

type ContentLine = Exclude<DiffLine, { kind: 'skip' }>;

const CONTEXT = 3;

const whole = (text: string): Segment[] => [{ text, changed: false }];

/** Пары «удалено → добавлено» одинаковой длины подсвечиваем по словам. */
function highlightWords(removed: ContentLine[], added: ContentLine[]) {
  if (removed.length !== added.length) return;
  removed.forEach((oldLine, index) => {
    const newLine = added[index];
    const oldText = oldLine.segments[0].text;
    const newText = newLine.segments[0].text;
    const parts = diffWordsWithSpace(oldText, newText);
    oldLine.segments = parts
      .filter((part) => !part.added)
      .map((part) => ({ text: part.value, changed: Boolean(part.removed) }));
    newLine.segments = parts
      .filter((part) => !part.removed)
      .map((part) => ({ text: part.value, changed: Boolean(part.added) }));
  });
}

/** Построчный diff Markdown с нумерацией, подсветкой слов и свёрткой неизменённых участков. */
export function lineDiff(before: string, after: string): DiffLine[] {
  const lines: ContentLine[] = [];
  let oldNumber = 1;
  let newNumber = 1;
  let pendingRemoved: ContentLine[] = [];

  for (const part of diffLines(before, after)) {
    const kind = part.added ? 'added' : part.removed ? 'removed' : 'same';
    const block = part.value
      .replace(/\n$/, '')
      .split('\n')
      .map((text): ContentLine => ({
        kind,
        segments: whole(text),
        oldNumber: kind === 'added' ? null : oldNumber++,
        newNumber: kind === 'removed' ? null : newNumber++,
      }));

    if (kind === 'added') highlightWords(pendingRemoved, block);
    pendingRemoved = kind === 'removed' ? block : [];
    lines.push(...block);
  }

  // Оставляем по CONTEXT строк вокруг изменений
  const keep = lines.map(() => false);
  lines.forEach((line, index) => {
    if (line.kind === 'same') return;
    const from = Math.max(0, index - CONTEXT);
    const to = Math.min(lines.length - 1, index + CONTEXT);
    for (let i = from; i <= to; i += 1) keep[i] = true;
  });

  const result: DiffLine[] = [];
  let skipped = 0;
  lines.forEach((line, index) => {
    if (keep[index]) {
      if (skipped) result.push({ kind: 'skip', count: skipped });
      skipped = 0;
      result.push(line);
    } else {
      skipped += 1;
    }
  });
  if (skipped) result.push({ kind: 'skip', count: skipped });
  return result;
}

export function diffStats(lines: DiffLine[]): {
  added: number;
  removed: number;
} {
  return lines.reduce(
    (stats, line) => ({
      added: stats.added + (line.kind === 'added' ? 1 : 0),
      removed: stats.removed + (line.kind === 'removed' ? 1 : 0),
    }),
    { added: 0, removed: 0 },
  );
}
