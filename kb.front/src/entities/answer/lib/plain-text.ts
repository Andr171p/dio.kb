import type { AnswerBlock } from '../model/types';

/** Плоский текст ответа для копирования в буфер. */
export function answerPlainText(blocks: AnswerBlock[]): string {
  return blocks
    .map((block) => block.markdown.trim())
    .filter(Boolean)
    .join('\n\n');
}
