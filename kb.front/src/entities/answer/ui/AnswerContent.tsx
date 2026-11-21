import Markdown, { defaultUrlTransform } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  inlineSourceIds,
  rewriteInlineCitations,
} from '../lib/rewrite-citations';
import type { AnswerBlock, AnswerSource } from '../model/types';
import { AnswerCitation } from './AnswerCitation';
import styles from './AnswerContent.module.scss';

interface AnswerContentProps {
  blocks: AnswerBlock[];
  sources: AnswerSource[];
}

/** `cite:` — внутренний протокол цитат; defaultUrlTransform его вырезает. */
function urlTransform(url: string): string {
  return url.startsWith('cite:') ? url : defaultUrlTransform(url);
}

/**
 * Рендер блоков ответа.
 * Сырые `src_N` в тексте LLM превращаются в кликабельные цитаты-превью.
 */
export function AnswerContent({ blocks, sources }: AnswerContentProps) {
  const byId = new Map(
    sources.map((source, index) => [source.id, { source, index: index + 1 }]),
  );

  return (
    <div className={styles.content}>
      {blocks.map((block, blockIndex) => {
        const rewritten = rewriteInlineCitations(block.markdown);
        const inlineIds = new Set(inlineSourceIds(block.markdown));
        const trailing = block.citations.filter((id) => !inlineIds.has(id));

        return (
          <div key={blockIndex} className={styles.block}>
            <Markdown
              remarkPlugins={[remarkGfm]}
              urlTransform={urlTransform}
              components={{
                a: ({ href, children }) => {
                  if (href?.startsWith('cite:')) {
                    const sourceId = href.slice('cite:'.length);
                    const entry = byId.get(sourceId);
                    return (
                      <AnswerCitation
                        index={entry?.index ?? 0}
                        source={entry?.source}
                      />
                    );
                  }
                  return (
                    <span className={styles.plainLink} title={href}>
                      {children}
                    </span>
                  );
                },
              }}
            >
              {rewritten}
            </Markdown>
            {trailing.length > 0 && (
              <span
                className={styles.citations}
                aria-label="Источники утверждения"
              >
                {trailing.map((sourceId) => {
                  const entry = byId.get(sourceId);
                  return (
                    <AnswerCitation
                      key={sourceId}
                      index={entry?.index ?? 0}
                      source={entry?.source}
                    />
                  );
                })}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
