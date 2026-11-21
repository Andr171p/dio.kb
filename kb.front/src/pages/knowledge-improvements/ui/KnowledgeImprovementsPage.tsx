import { useEffect, useEffectEvent, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import {
  assignKnowledgeGapOwner,
  classifyKnowledgeGap,
  completeKnowledgeGap,
  GAP_KIND_ACTION,
  GAP_KIND_LABELS,
  GAP_STATUS_LABELS,
  loadKnowledgeGap,
  loadKnowledgeGaps,
  rejectKnowledgeGap,
  reopenSelectedKnowledgeGap,
  takeKnowledgeGap,
  useKnowledgeGaps,
  type GapKind,
  type GapStatus,
} from '@entities/knowledge-gap';
import { useCurrentUser } from '@entities/session';
import { loadSpaces, useSpaces } from '@entities/space';
import { SidebarToggle } from '@widgets/app-sidebar';
import { ImprovementInbox } from '@widgets/improvement-inbox';
import { describeError } from '@shared/api';
import { routes } from '@shared/config/routes';
import { Breadcrumbs } from '@shared/ui/breadcrumbs';
import { Button } from '@shared/ui/button';
import { Notice } from '@shared/ui/notice';
import { Topbar } from '@shared/ui/topbar';
import { toast } from '@shared/ui/toast';
import styles from './KnowledgeImprovementsPage.module.scss';

const EDITABLE_KINDS: GapKind[] = [
  'missing_content',
  'incomplete_content',
  'outdated_content',
  'conflicting_content',
  'discoverability',
];

export function KnowledgeImprovementsPage() {
  const { gapId } = useParams();
  const navigate = useNavigate();
  const user = useCurrentUser();
  const spaces = useSpaces((state) => state.items);
  const { status, items, error, selected, selectedError, selectedLoading } =
    useKnowledgeGaps();
  const [filter, setFilter] = useState<GapStatus | 'all'>('open');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);

  const onOpenList = useEffectEvent(() => {
    void loadSpaces();
    void loadKnowledgeGaps();
  });

  useEffect(() => {
    onOpenList();
  }, []);

  useEffect(() => {
    if (!gapId) return;
    void loadKnowledgeGap(gapId);
  }, [gapId]);

  const selectedNote = selected?.resolutionNote ?? '';
  const [noteSyncedFor, setNoteSyncedFor] = useState<string | null>(null);
  if (gapId && selected?.id === gapId && noteSyncedFor !== selected.id) {
    setNoteSyncedFor(selected.id);
    setNote(selectedNote);
  }
  if (!gapId && noteSyncedFor !== null) {
    setNoteSyncedFor(null);
    setNote('');
  }

  const totals = useMemo(() => {
    const result: Partial<Record<GapStatus, number>> = {};
    for (const item of items) {
      result[item.status] = (result[item.status] ?? 0) + 1;
    }
    return result;
  }, [items]);

  const visibleItems = useMemo(
    () =>
      filter === 'all' ? items : items.filter((item) => item.status === filter),
    [filter, items],
  );

  const runAction = async (action: () => Promise<void>) => {
    setBusy(true);
    try {
      await action();
      toast.success('Изменение сохранено');
    } catch (actionError) {
      toast.error(describeError(actionError));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Topbar
        start={
          <>
            <SidebarToggle />
            <Breadcrumbs
              items={[
                {
                  label: 'Улучшения знаний',
                  to: routes.knowledgeImprovements(),
                },
                ...(selected ? [{ label: selected.title }] : []),
              ]}
            />
          </>
        }
      />
      <div className={styles.page}>
        {!gapId && (
          <>
            <header className={styles.intro}>
              <h1 className={styles.title}>Улучшения знаний</h1>
              <p className={styles.lead}>
                Повторяющиеся проблемы поиска и AI-ответов. Классифицируйте,
                назначьте ответственного и закройте после правки статьи.
              </p>
            </header>
            <ImprovementInbox
              items={visibleItems}
              spaces={spaces}
              status={status === 'idle' ? 'loading' : status}
              error={error}
              filter={filter}
              onFilter={setFilter}
              totals={totals}
            />
          </>
        )}

        {gapId && selectedError && <Notice>{selectedError}</Notice>}
        {gapId && selectedLoading && !selected && (
          <p className={styles.lead}>Загрузка…</p>
        )}

        {gapId && selected && (
          <div className={styles.detail}>
            <div className={styles.detailMain}>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => void navigate(routes.knowledgeImprovements())}
              >
                ← К списку
              </Button>
              <h1 className={styles.title}>{selected.title}</h1>
              <p className={styles.meta}>
                {GAP_KIND_LABELS[selected.kind]} ·{' '}
                {GAP_STATUS_LABELS[selected.status]} · {selected.signalCount}{' '}
                сигналов
              </p>
              {selected.rationale && (
                <p className={styles.rationale}>{selected.rationale}</p>
              )}
              <p className={styles.recommendation}>
                Рекомендация: {GAP_KIND_ACTION[selected.kind]}
              </p>
              {selected.relatedArticleId && (
                <Button
                  size="sm"
                  onClick={() =>
                    void navigate(
                      routes.editArticle(selected.relatedArticleId!),
                    )
                  }
                >
                  Улучшить статью
                </Button>
              )}
            </div>

            <aside className={styles.detailSide}>
              <h2 className={styles.sideTitle}>Действия</h2>

              {selected.status === 'open' && (
                <>
                  <label className={styles.field}>
                    Категория
                    <select
                      className={styles.select}
                      value={selected.kind}
                      disabled={busy}
                      onChange={(event) =>
                        void runAction(() =>
                          classifyKnowledgeGap(
                            selected.id,
                            event.target.value as GapKind,
                          ),
                        )
                      }
                    >
                      {EDITABLE_KINDS.map((kind) => (
                        <option key={kind} value={kind}>
                          {GAP_KIND_LABELS[kind]}
                        </option>
                      ))}
                      <option value="needs_triage">
                        {GAP_KIND_LABELS.needs_triage}
                      </option>
                    </select>
                  </label>

                  {selected.kind !== 'needs_triage' && (
                    <Button
                      block
                      loading={busy}
                      onClick={() =>
                        void runAction(() => takeKnowledgeGap(selected.id))
                      }
                    >
                      Взять в работу
                    </Button>
                  )}

                  {user && (
                    <Button
                      block
                      variant="secondary"
                      loading={busy}
                      onClick={() =>
                        void runAction(() =>
                          assignKnowledgeGapOwner(selected.id, user.id),
                        )
                      }
                    >
                      Назначить на меня
                    </Button>
                  )}

                  <label className={styles.field}>
                    Причина отклонения
                    <textarea
                      className={styles.textarea}
                      rows={3}
                      value={note}
                      onChange={(event) => setNote(event.target.value)}
                    />
                  </label>
                  <Button
                    block
                    variant="ghost"
                    loading={busy}
                    disabled={note.trim().length < 1}
                    onClick={() =>
                      void runAction(() =>
                        rejectKnowledgeGap(selected.id, note.trim()),
                      )
                    }
                  >
                    Отклонить
                  </Button>
                </>
              )}

              {selected.status === 'in_progress' && (
                <>
                  <label className={styles.field}>
                    Что сделано
                    <textarea
                      className={styles.textarea}
                      rows={4}
                      value={note}
                      onChange={(event) => setNote(event.target.value)}
                    />
                  </label>
                  <Button
                    block
                    loading={busy}
                    disabled={note.trim().length < 1}
                    onClick={() =>
                      void runAction(() =>
                        completeKnowledgeGap(selected.id, note.trim()),
                      )
                    }
                  >
                    Завершить
                  </Button>
                  <Button
                    block
                    variant="ghost"
                    loading={busy}
                    disabled={note.trim().length < 1}
                    onClick={() =>
                      void runAction(() =>
                        rejectKnowledgeGap(selected.id, note.trim()),
                      )
                    }
                  >
                    Отклонить
                  </Button>
                </>
              )}

              {(selected.status === 'resolved' ||
                selected.status === 'dismissed') && (
                <>
                  {selected.resolutionNote && (
                    <p className={styles.rationale}>{selected.resolutionNote}</p>
                  )}
                  <Button
                    block
                    loading={busy}
                    onClick={() =>
                      void runAction(() =>
                        reopenSelectedKnowledgeGap(selected.id),
                      )
                    }
                  >
                    Переоткрыть
                  </Button>
                </>
              )}
            </aside>
          </div>
        )}
      </div>
    </>
  );
}
