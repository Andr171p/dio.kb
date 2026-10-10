import { describe, expect, test } from 'vitest';
import { diffStats, lineDiff } from './line-diff';

describe('lineDiff', () => {
  test('помечает добавленные и удалённые строки с номерами', () => {
    const lines = lineDiff('a\nb\nc\n', 'a\nx\nc\n');
    expect(
      lines.map((line) =>
        line.kind === 'skip'
          ? 'skip'
          : [line.kind, line.oldNumber, line.newNumber],
      ),
    ).toEqual([
      ['same', 1, 1],
      ['removed', 2, null],
      ['added', null, 2],
      ['same', 3, 3],
    ]);
    expect(diffStats(lines)).toEqual({ added: 1, removed: 1 });
  });

  test('подсвечивает изменённые слова в парных строках', () => {
    const [removed, added] = lineDiff('Срок 2 часа\n', 'Срок 4 часа\n');
    if (removed.kind === 'skip' || added.kind === 'skip')
      throw new Error('unexpected skip');
    expect(
      removed.segments.filter((segment) => segment.changed).map((s) => s.text),
    ).toEqual(['2']);
    expect(
      added.segments.filter((segment) => segment.changed).map((s) => s.text),
    ).toEqual(['4']);
  });

  test('сворачивает неизменённые участки дальше трёх строк от правки', () => {
    const before = Array.from({ length: 20 }, (_, i) => `line ${i}`).join('\n');
    const after = before.replace('line 10', 'changed');
    const lines = lineDiff(before, after);
    expect(lines[0]).toEqual({ kind: 'skip', count: 7 });
    expect(lines.at(-1)).toEqual({ kind: 'skip', count: 6 });
  });
});
