import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { AnswerBlock, AnswerSource } from '../model/types';
import { AnswerCitation } from './AnswerCitation';
import styles from './AnswerContent.module.scss';

interface AnswerContentProps {
  blocks: AnswerBlock[];
  sources: AnswerSource[];
  onPreviewSource?: (source: AnswerSource) => void;
}

/**
 * Рендер блоков ответа. Citations из поля blocks.citations —
 * не из произвольных ссылок LLM в Markdown.
 */
export function AnswerContent({
  blocks,
  sources,
  onPreviewSource,
}: AnswerContentProps) {
  const byId = new Map(sources.map((source, index) => [source.id, { source, index: index + 1 }]));

  return (
    <div className={styles.content}>
      {blocks.map((block, blockIndex) => (
        <div key={blockIndex} className={styles.block}>
          <Markdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ href, children }) => (
                <span className={styles.plainLink} title={href}>
                  {children}
                </span>
              ),
            }}
          >
            {block.markdown}
          </Markdown>
          {block.citations.length > 0 && (
            <span className={styles.citations} aria-label="Источники утверждения">
              {block.citations.map((sourceId) => {
                const entry = byId.get(sourceId);
                return (
                  <AnswerCitation
                    key={sourceId}
                    index={entry?.index ?? 0}
                    source={entry?.source}
                    onPreview={onPreviewSource}
                  />
                );
              })}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

