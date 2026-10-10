import { describe, expect, test } from 'vitest';
import { normalizeMarkdown } from './markdown';

describe('normalizeMarkdown', () => {
  test('схлопывает лишние пустые строки вне кода', () => {
    expect(normalizeMarkdown('# A\n\n\n\n| a |\n| - |\n\n\ntext')).toBe(
      '# A\n\n| a |\n| - |\n\ntext\n',
    );
  });

  test('не меняет содержимое блоков кода', () => {
    const md = '```py\nx = 1\n\n\n\ny = 2  \n```';
    expect(normalizeMarkdown(md)).toBe(`${md}\n`);
  });

  test('сворачивает ссылку на саму себя в «голый» URL, кроме кода', () => {
    expect(
      normalizeMarkdown(
        'См. [https://a.ru/x](https://a.ru/x) и [сайт](https://a.ru)\n\n```\n[https://b](https://b)\n```',
      ),
    ).toBe(
      'См. https://a.ru/x и [сайт](https://a.ru)\n\n```\n[https://b](https://b)\n```\n',
    );
  });

  test('сохраняет перенос строки (два пробела) и нормализует CRLF', () => {
    expect(normalizeMarkdown('a  \r\nb\r\n\r\n\r\n')).toBe('a  \nb\n');
  });
});
