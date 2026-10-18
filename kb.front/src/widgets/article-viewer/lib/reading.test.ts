import { describe, expect, it } from 'vitest';
import { readingMinutes, relatedArticles } from './reading';

const ID_A = '01a12790-9b50-76a2-a869-a2651ecff3dc';
const ID_B = '01a12790-9b50-76a2-a869-a2651ecff3dd';
const CURRENT = '01a12790-9b50-76a2-a869-a2651ecff3de';

describe('readingMinutes', () => {
  it('не меньше минуты для короткого текста', () => {
    expect(readingMinutes('Коротко.')).toBe(1);
  });

  it('считает слова, а не разметку ссылок и картинок', () => {
    const words = Array.from({ length: 360 }, () => 'слово').join(' ');
    const markdown = `${words}\n\n![схема](media://abc) [ссылка](https://example.com/very/long/path)`;
    expect(readingMinutes(markdown)).toBe(2);
  });
});

describe('relatedArticles', () => {
  it('берёт ссылки на статьи базы без дублей и без текущей статьи', () => {
    const markdown = [
      `См. [Настройка **VPN**](/articles/${ID_A}) и [ещё раз](/articles/${ID_A}).`,
      `[Сама статья](/articles/${CURRENT})`,
      `[Восстановление](${window.location.origin}/articles/${ID_B}#шаги)`,
    ].join('\n');

    expect(relatedArticles(markdown, CURRENT)).toEqual([
      { id: ID_A, title: 'Настройка VPN' },
      { id: ID_B, title: 'Восстановление' },
    ]);
  });

  it('игнорирует внешние ссылки и изображения', () => {
    const markdown = `[Сайт](https://example.com) ![картинка](/articles/${ID_A})`;
    expect(relatedArticles(markdown, CURRENT)).toEqual([]);
  });

  it('ограничивает количество', () => {
    const ids = Array.from(
      { length: 7 },
      (_, index) =>
        `01a12790-9b50-76a2-a869-a2651ecff3${String(index).padStart(2, '0')}`,
    );
    const markdown = ids
      .map((id, index) => `[Статья ${index}](/articles/${id})`)
      .join(' ');
    expect(relatedArticles(markdown, CURRENT, 3)).toHaveLength(3);
  });
});
