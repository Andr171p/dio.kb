import { Link2 } from 'lucide-react';
import { useState } from 'react';
import Markdown from 'react-markdown';
import { Link } from 'react-router';
import type { AnswerSource } from '@entities/answer';
import { routes } from '@shared/config/routes';
import { KnowledgeMark } from '@shared/ui/logo';
import styles from './AnswerSources.module.scss';

const COLLAPSED_COUNT = 3;

interface AnswerSourcesProps {
  sources: AnswerSource[];
}

/** Источники в стиле Atlassian: клик сразу открывает статью с якорем. */
export function AnswerSources({ sources }: AnswerSourcesProps) {
  const [expanded, setExpanded] = useState(false);
  const needsCollapse = sources.length > COLLAPSED_COUNT;
  const visible =
    needsCollapse && !expanded
      ? sources.slice(0, COLLAPSED_COUNT)
      : sources;

  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <Link2 size={14} aria-hidden />
        Источники
      </header>

      <aside className={styles.panel} aria-label="Источники">
        {sources.length === 0 ? (
          <p className={styles.empty}>Нет подтверждённых источников</p>
        ) : (
          <>
            <ol className={styles.list}>
              {visible.map((source) => (
                <li key={source.id} className={styles.row}>
                  <Link
                    to={routes.article(source.articleId, source.anchor)}
                    className={styles.item}
                  >
                    <KnowledgeMark size={16} />
                    <span className={styles.body}>
                      <span className={styles.title}>{source.title}</span>
                      {source.excerpt && (
                        <span className={styles.excerpt}>
                          <Markdown
                            components={{
                              p: ({ children }) => <span>{children}</span>,
                              a: ({ children }) => <span>{children}</span>,
                              ul: ({ children }) => <span>{children}</span>,
                              ol: ({ children }) => <span>{children}</span>,
                              li: ({ children }) => <span>{children} </span>,
                              strong: ({ children }) => (
                                <strong>{children}</strong>
                              ),
                              em: ({ children }) => <em>{children}</em>,
                              code: ({ children }) => (
                                <code className={styles.inlineCode}>
                                  {children}
                                </code>
                              ),
                              pre: ({ children }) => <span>{children}</span>,
                              h1: ({ children }) => <strong>{children}</strong>,
                              h2: ({ children }) => <strong>{children}</strong>,
                              h3: ({ children }) => <strong>{children}</strong>,
                            }}
                          >
                            {source.excerpt}
                          </Markdown>
                        </span>
                      )}
                    </span>
                  </Link>
                </li>
              ))}
            </ol>
            {needsCollapse && (
              <button
                type="button"
                className={styles.toggle}
                onClick={() => setExpanded((value) => !value)}
              >
                {expanded ? 'Свернуть' : 'Показать ещё'}
              </button>
            )}
          </>
        )}
      </aside>
    </div>
  );
}
