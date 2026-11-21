import { TriangleAlert } from 'lucide-react';
import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import {
  answerPlainText,
  AnswerContent,
  progressLabel,
  type AnswerSource,
} from '@entities/answer';
import { AnswerFeedback } from '@features/answer-feedback';
import {
  resetAnswerRun,
  retryAnswerRun,
  startAnswerRun,
  useAnswerRun,
} from '@features/answer-generation';
import { routes } from '@shared/config/routes';
import { useMediaQuery } from '@shared/lib/hooks';
import { Button } from '@shared/ui/button';
import { KnowledgeMark } from '@shared/ui/logo';
import { AnswerSources } from './AnswerSources';
import styles from './AnswerPanel.module.scss';

interface AnswerPanelProps {
  query: string;
  spaceIds: string[];
  onAnswerIdChange?: (answerId: string | null) => void;
}

const COLLAPSED_MAX = 520;

/** Ответ от ИИ: CTA / светящаяся плашка прогресса / ответ + источники. */
export function AnswerPanel(props: AnswerPanelProps) {
  const answerId = useAnswerRun((state) => state.answerId);
  return <AnswerPanelView key={answerId ?? 'idle'} {...props} />;
}

function AnswerPanelView({
  query,
  spaceIds,
  onAnswerIdChange,
}: AnswerPanelProps) {
  const state = useAnswerRun();
  const compact = useMediaQuery('(max-width: 900px)');
  const [expanded, setExpanded] = useState(false);
  const [preview, setPreview] = useState<AnswerSource | null>(null);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [, setParams] = useSearchParams();

  const trimmed = query.trim();
  const canAsk = trimmed.length >= 2;
  const label = progressLabel({
    status: state.progress?.status ?? 'queued',
    stage: state.progress?.stage ?? null,
    resultsCount: state.progress?.resultsCount,
    sourcesCount: state.progress?.sourcesCount,
    connection:
      state.connection === 'reconnecting' ? 'reconnecting' : undefined,
  });

  const writeAnswerParam = (nextAnswerId: string | null) => {
    onAnswerIdChange?.(nextAnswerId);
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (nextAnswerId) next.set('answer', nextAnswerId);
        else next.delete('answer');
        next.delete('ai');
        return next;
      },
      { replace: true },
    );
  };

  if (state.phase === 'idle') {
    if (!canAsk) return null;
    return (
      <section className={styles.cta} aria-label="Ответ от ИИ">
        <div className={styles.ctaText}>
          <KnowledgeMark size={22} />
          <div>
            <p className={styles.ctaTitle}>Получить ответ от ИИ</p>
            <p className={styles.ctaHint}>
              Обоснованный ответ по доступным вам статьям — только по вашему
              запросу.
            </p>
          </div>
        </div>
        <Button
          variant="secondary"
          onClick={() =>
            void startAnswerRun({ question: trimmed, spaceIds }).then((id) => {
              if (id) writeAnswerParam(id);
            })
          }
        >
          Спросить
        </Button>
      </section>
    );
  }

  if (state.phase === 'starting' || state.phase === 'running') {
    return (
      <section className={styles.progressWrap} aria-live="polite" aria-busy>
        <div
          className={styles.progressPlaque}
          key={`${state.progress?.sequence ?? 0}-${label}`}
        >
          <KnowledgeMark size={20} />
          <p className={styles.progressText}>{label}</p>
        </div>
      </section>
    );
  }

  if (
    state.phase === 'failed' ||
    state.phase === 'cancelled' ||
    state.phase === 'access_denied'
  ) {
    return (
      <section className={styles.error} role="alert">
        <div className={styles.errorHead}>
          <TriangleAlert size={16} aria-hidden />
          <p>
            {state.error ??
              (state.phase === 'cancelled'
                ? 'Генерация отменена'
                : 'Не удалось получить ответ')}
          </p>
        </div>
        <div className={styles.errorActions}>
          {(state.phase === 'failed' || state.phase === 'cancelled') && (
            <Button
              size="sm"
              onClick={() =>
                void retryAnswerRun().then((id) => {
                  if (id) writeAnswerParam(id);
                })
              }
            >
              Попробовать снова
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              resetAnswerRun();
              writeAnswerParam(null);
            }}
          >
            Скрыть
          </Button>
        </div>
      </section>
    );
  }

  const response = state.run?.response;
  if (!response) return null;

  const plain = answerPlainText(response.blocks);
  const needsCollapse = plain.length > COLLAPSED_MAX;
  const showCollapsed = needsCollapse && !expanded;

  return (
    <section className={styles.root} aria-label="Ответ от ИИ">
      <div className={styles.layout}>
        <div className={styles.main}>
          <header className={styles.header}>
            <KnowledgeMark size={18} />
            Ответ от ИИ
            {response.status !== 'answered' && (
              <span className={styles.badge}>
                {response.status === 'insufficient_evidence'
                  ? 'Недостаточно оснований'
                  : 'Противоречивые источники'}
              </span>
            )}
          </header>

          <div className={showCollapsed ? styles.collapsed : undefined}>
            <AnswerContent
              blocks={response.blocks}
              sources={response.sources}
              onPreviewSource={(source) => {
                setPreview(source);
                if (compact) setSourcesOpen(true);
              }}
            />
          </div>

          {needsCollapse && (
            <button
              type="button"
              className={styles.showMore}
              onClick={() => setExpanded((value) => !value)}
            >
              {expanded ? 'Свернуть' : 'Показать ещё'}
            </button>
          )}

          {response.missingContext.length > 0 && (
            <ul className={styles.missing}>
              {response.missingContext.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}

          {compact && response.sources.length > 0 && (
            <button
              type="button"
              className={styles.sourcesToggle}
              onClick={() => setSourcesOpen((value) => !value)}
            >
              {sourcesOpen
                ? 'Скрыть источники'
                : `Источники (${response.sources.length})`}
            </button>
          )}

          <AnswerFeedback answerId={response.id} copyText={plain} />
        </div>

        {(!compact || sourcesOpen) && (
          <div className={styles.side}>
            <AnswerSources
              sources={response.sources}
              activeId={preview?.id}
              onSelect={setPreview}
            />
            {preview && (
              <div className={styles.preview}>
                <p className={styles.previewTitle}>{preview.title}</p>
                <div className={styles.previewExcerpt}>
                  <AnswerContent
                    blocks={[{ markdown: preview.excerpt, citations: [] }]}
                    sources={[]}
                  />
                </div>
                <Link
                  className={styles.previewLink}
                  to={routes.article(preview.articleId, preview.anchor)}
                >
                  Открыть раздел статьи
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
      <hr className={styles.divider} />
    </section>
  );
}
