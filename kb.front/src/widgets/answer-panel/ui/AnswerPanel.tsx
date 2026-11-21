import { TriangleAlert } from 'lucide-react';
import { useState } from 'react';
import { useSearchParams } from 'react-router';
import {
  answerPlainText,
  AnswerContent,
  progressLabel,
} from '@entities/answer';
import { AnswerFeedback } from '@features/answer-feedback';
import {
  resetAnswerRun,
  retryAnswerRun,
  startAnswerRun,
  useAnswerRun,
} from '@features/answer-generation';
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
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [, setParams] = useSearchParams();

  const trimmed = query.trim();
  const canAsk = trimmed.length >= 2;
  const matchesCurrentAnswer =
    Boolean(state.question) && state.question!.trim() === trimmed;

  const label = progressLabel({
    status: state.progress?.status ?? 'queued',
    stage: state.progress?.stage ?? null,
    resultsCount: state.progress?.resultsCount,
    sourcesCount: state.progress?.sourcesCount,
    connection:
      state.connection === 'reconnecting' ? 'reconnecting' : undefined,
  });

  const writeAnswerParam = (
    nextAnswerId: string | null,
    question = trimmed,
  ) => {
    onAnswerIdChange?.(nextAnswerId);
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (question) next.set('q', question);
        if (nextAnswerId) next.set('answer', nextAnswerId);
        else next.delete('answer');
        next.delete('ai');
        return next;
      },
      { replace: true },
    );
  };

  const askAi = () => {
    // Сразу синхронизируем q в URL — иначе эффект на SearchPage
    // сбросит run, пока urlQuery ещё старый.
    writeAnswerParam(null, trimmed);
    void startAnswerRun({ question: trimmed, spaceIds }).then((id) => {
      if (id) writeAnswerParam(id, trimmed);
    });
  };

  const showCta =
    canAsk &&
    (state.phase === 'idle' ||
      ((state.phase === 'ready' ||
        state.phase === 'failed' ||
        state.phase === 'cancelled' ||
        state.phase === 'access_denied') &&
        !matchesCurrentAnswer));

  if (showCta) {
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
          // Не даём input потерять фокус до click — blur иначе
          // коммитит поиск и гоняется со startAnswerRun.
          onMouseDown={(event) => event.preventDefault()}
          onClick={askAi}
        >
          Спросить
        </Button>
      </section>
    );
  }

  if (
    (state.phase === 'starting' || state.phase === 'running') &&
    matchesCurrentAnswer
  ) {
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
    (state.phase === 'failed' ||
      state.phase === 'cancelled' ||
      state.phase === 'access_denied') &&
    matchesCurrentAnswer
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

  if (state.phase !== 'ready' || !matchesCurrentAnswer) return null;

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
            <AnswerSources sources={response.sources} />
          </div>
        )}
      </div>
      <hr className={styles.divider} />
    </section>
  );
}
