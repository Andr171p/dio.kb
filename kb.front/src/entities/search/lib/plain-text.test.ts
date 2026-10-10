import { describe, expect, test } from 'vitest';
import { markdownToSnippet } from './plain-text';

describe('markdownToSnippet', () => {
  test('убирает разметку таблиц, но сохраняет подчёркивания в словах', () => {
    const md =
      '| Код | Причина |\n|---|---|\n| AUTH_FAILED | Неверный пароль |';
    expect(markdownToSnippet(md)).toBe(
      'Код Причина AUTH_FAILED Неверный пароль',
    );
  });

  test('убирает отметки чеклиста, заголовки и выделение', () => {
    const md =
      '## Шаги\n\n- [x] **Проверить** _контакты_\n- [ ] Закрыть `заявку`';
    expect(markdownToSnippet(md)).toBe(
      'Шаги Проверить контакты Закрыть заявку',
    );
  });

  test('оставляет текст ссылок, убирает картинки и код', () => {
    const md =
      'См. [статью](/articles/1) ![схема](media://x)\n```bash\nrm -rf\n```\nконец';
    expect(markdownToSnippet(md)).toBe('См. статью конец');
  });

  test('обрезает длинный текст многоточием', () => {
    expect(markdownToSnippet('слово '.repeat(100), 20)).toHaveLength(20);
  });
});
