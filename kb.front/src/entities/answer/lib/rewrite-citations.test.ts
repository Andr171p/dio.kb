import { describe, expect, it } from 'vitest';
import {
  inlineSourceIds,
  rewriteInlineCitations,
} from './rewrite-citations';

describe('rewriteInlineCitations', () => {
  it('replaces bare and wrapped src_N', () => {
    expect(rewriteInlineCitations('см. src_1 и (src_2)')).toBe(
      'см. [1](cite:src_1) и [2](cite:src_2)',
    );
  });

  it('does not eat closing paren of see-also group', () => {
    const input =
      'Проверьте группу 1C_Users (см. src_1, src_2, src_3).';
    expect(rewriteInlineCitations(input)).toBe(
      'Проверьте группу 1C_Users (см. [1](cite:src_1), [2](cite:src_2), [3](cite:src_3)).',
    );
  });

  it('collects unique source ids', () => {
    expect(inlineSourceIds('a src_1 b src_1 c (src_2)')).toEqual([
      'src_1',
      'src_2',
    ]);
  });
});
