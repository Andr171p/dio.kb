import { describe, expect, it } from 'vitest';
import { formatDayTime, pluralize } from './format';

describe('pluralize', () => {
  const forms: [string, string, string] = ['статья', 'статьи', 'статей'];

  it.each([
    [1, '1 статья'],
    [3, '3 статьи'],
    [5, '5 статей'],
    [11, '11 статей'],
    [21, '21 статья'],
    [0, '0 статей'],
  ])('%i → %s', (count, expected) => {
    expect(pluralize(count, forms)).toBe(expected);
  });
});

describe('formatDayTime', () => {
  it('«12 октября, 14:25» без года и предлога', () => {
    expect(formatDayTime(new Date(2026, 9, 12, 14, 25))).toBe(
      '12 октября, 14:25',
    );
  });
});
