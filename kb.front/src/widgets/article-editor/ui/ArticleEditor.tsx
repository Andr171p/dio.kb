import DragHandle from '@tiptap/extension-drag-handle-react';
import { EditorContent, useEditorState } from '@tiptap/react';
import clsx from 'clsx';
import { ChevronDown, GripVertical } from 'lucide-react';
import { useState, type ReactNode } from 'react';
import { hasPermission, type Permission } from '@entities/access-grant';
import type { ArticleDetail } from '@entities/article';
import { routes } from '@shared/config/routes';
import { formatRelative, pluralize } from '@shared/lib/format';
import { MOD_KEY_LABEL, useCopyToClipboard } from '@shared/lib/hooks';
import { Button, ButtonLink } from '@shared/ui/button';
import { Callout } from '@shared/ui/callout';
import { Dialog, DialogActions } from '@shared/ui/dialog';
import { EmptyState } from '@shared/ui/empty-state';
import { TextAreaField } from '@shared/ui/field';
import { Popover, usePopover } from '@shared/ui/popover';
import { toast } from '@shared/ui/toast';
import {
  useArticleEditor,
  type EditorTarget,
} from '../model/use-article-editor';
import { TableToolbar } from './EditorToolbar';
import { FormatToolbar } from './FormatToolbar';
import styles from './ArticleEditor.module.scss';

interface ArticleEditorProps {
  target: EditorTarget;
  /** Права в пространстве (для новой статьи) или на статью */
  permissions: Permission[];
  onCreated: (detail: ArticleDetail) => void;
  onPublished: (detail: ArticleDetail) => void;
  /** Предпросмотр Markdown тем же рендером, что и при чтении */
  renderPreview: (markdown: string) => ReactNode;
  /** Шапка страницы: редактор передаёт в неё состояние и кнопки сохранения */
  renderHeader: (actions: ReactNode) => ReactNode;
}

function SaveButton({
  dirty,
  saving,
  onSave,
}: {
  dirty: boolean;
  saving: boolean;
  onSave: (changeNote: string | null) => void;
}) {
  const { triggerProps, popoverProps } = usePopover();
  const [note, setNote] = useState('');

  return (
    <div className={styles.split}>
      <Button
        loading={saving}
        disabled={!dirty}
        className={styles.splitMain}
        title={`Сохранить новую редакцию (${MOD_KEY_LABEL}+S)`}
        onClick={() => onSave(null)}
      >
        Сохранить
      </Button>
      <button
        type="button"
        className={styles.splitToggle}
        aria-label="Сохранить с комментарием"
        disabled={!dirty || saving}
        {...triggerProps}
      >
        <ChevronDown size={15} aria-hidden />
      </button>
      <Popover
        {...popoverProps}
        placement="bottom-end"
        className={styles.notePopover}
      >
        <form
          className={styles.noteForm}
          onSubmit={(event) => {
            event.preventDefault();
            onSave(note.trim() || null);
            setNote('');
            document.getElementById(popoverProps.id)?.hidePopover();
          }}
        >
          <TextAreaField
            label="Что изменено"
            value={note}
            rows={3}
            placeholder="Например: обновил таблицу приоритетов"
            hint="Комментарий увидят в истории редакций"
            onChange={(event) => setNote(event.target.value)}
          />
          <Button type="submit" variant="primary">
            Сохранить редакцию
          </Button>
        </form>
      </Popover>
    </div>
  );
}

/** Редактор статьи: Markdown остаётся каноническим форматом, сохранение создаёт новую редакцию. */
export function ArticleEditor({
  target,
  permissions,
  onCreated,
  onPublished,
  renderPreview,
  renderHeader,
}: ArticleEditorProps) {
  const state = useArticleEditor(target, { onCreated, onPublished });
  const { editor, detail, dirty, status } = state;
  const { copy } = useCopyToClipboard();
  const [preview, setPreview] = useState<string | null>(null);
  const canPublish = hasPermission(permissions, 'PUBLISH');

  const stats = useEditorState({
    editor,
    selector: ({ editor: current }) => ({
      words:
        (current?.storage.characterCount.words() as number | undefined) ?? 0,
    }),
  });

  const article = detail?.article;
  const published = Boolean(article?.publishedRevisionId);
  const unpublished = published && (article?.hasUnpublishedChanges || dirty);
  const isDraft = !article || article.status === 'draft' || unpublished;

  const stateLabel = !detail
    ? 'Новая статья · черновик'
    : `${isDraft ? 'Черновик' : 'Опубликовано'} · редакция ${detail.revision.number}`;

  const saveState = [
    dirty ? 'Локальная копия сохранена' : detail ? 'Изменения сохранены' : null,
    detail
      ? `на сервере редакция ${detail.revision.number}`
      : 'Серверная редакция ещё не создана',
    pluralize(stats.words, ['слово', 'слова', 'слов']),
  ]
    .filter(Boolean)
    .join(' · ');

  return (
    <>
      {renderHeader(
        <>
          <span
            className={clsx(styles.state, isDraft && styles.stateDraft)}
            aria-live="polite"
          >
            {stateLabel}
          </span>
          <SaveButton
            dirty={dirty || !detail}
            saving={status === 'saving'}
            onSave={(note) => void state.save(note)}
          />
          {canPublish && (
            <Button
              variant="primary"
              loading={status === 'publishing'}
              disabled={status !== 'idle'}
              onClick={() => void state.publish()}
            >
              Опубликовать
            </Button>
          )}
        </>,
      )}
      <div className={styles.page}>
        {state.conflict ? (
          <EmptyState
            tone="warning"
            className={styles.notice}
            title="Статья изменилась, пока вы её редактировали"
            description="Ваш текст сохранён локально. Сравните изменения перед сохранением новой редакции — предыдущая редакция останется в истории."
            action={
              <>
                {detail && (
                  <ButtonLink
                    to={routes.articleHistory(detail.article.id)}
                    target="_blank"
                  >
                    Сравнить изменения
                  </ButtonLink>
                )}
                <Button
                  onClick={() =>
                    void copy(state.getContent()).then(() =>
                      toast.success('Ваш текст скопирован в буфер обмена'),
                    )
                  }
                >
                  Скопировать мой текст
                </Button>
                <Button
                  variant="primary"
                  loading={status === 'saving'}
                  onClick={() => void state.overwrite()}
                >
                  Сохранить поверх
                </Button>
              </>
            }
          />
        ) : (
          isDraft && (
            <p className={styles.band} role="status">
              {published
                ? 'Есть неопубликованные изменения. Читатели видят опубликованную редакцию.'
                : 'Статья ещё не опубликована — её видят только редакторы пространства.'}
            </p>
          )
        )}

        {state.restorable && (
          <Callout
            className={styles.notice}
            title="Найдены несохранённые изменения"
            actions={
              <>
                <Button onClick={state.discardRestorable}>Удалить</Button>
                <Button variant="primary" onClick={state.restore}>
                  Восстановить
                </Button>
              </>
            }
          >
            Версия от {formatRelative(state.restorable.savedAt)} осталась в этом
            браузере
            {state.restorable.baseRevisionId &&
            detail &&
            state.restorable.baseRevisionId !== detail.revision.id
              ? ' и основана на более старой редакции'
              : ''}
            .
          </Callout>
        )}

        <div className={styles.document} hidden={preview !== null}>
          <textarea
            id="article-title"
            className={styles.title}
            value={state.title}
            placeholder="Название статьи"
            rows={1}
            maxLength={255}
            aria-label="Название статьи"
            autoFocus={!detail}
            onChange={(event) =>
              state.setTitle(event.target.value.replace(/\n/g, ' '))
            }
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault();
                editor?.commands.focus('start');
              }
            }}
          />
          <label className={styles.summaryLabel} htmlFor="article-summary">
            Краткое описание
          </label>
          <textarea
            id="article-summary"
            className={styles.summary}
            value={state.summary}
            rows={1}
            placeholder="Пара предложений о главном — показывается в блоке «Коротко», поиске и превью ссылок"
            onChange={(event) =>
              state.setSummary(event.target.value.replace(/\n/g, ' '))
            }
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault();
                editor?.commands.focus('start');
              }
            }}
          />

          <div className={styles.editorArea}>
            {editor && (
              <>
                <FormatToolbar editor={editor} />
                <DragHandle editor={editor} className={styles.dragHandle}>
                  <GripVertical size={14} aria-hidden />
                </DragHandle>
                <TableToolbar editor={editor} />
              </>
            )}
            <EditorContent editor={editor} className={styles.content} />
          </div>
        </div>

        {preview !== null && (
          <div className={styles.preview}>
            <h1 className={styles.previewTitle}>
              {state.title.trim() || 'Без названия'}
            </h1>
            {state.summary.trim() && (
              <section className={styles.previewSummary}>
                <p className={styles.previewSummaryLabel}>Коротко</p>
                <p>{state.summary}</p>
              </section>
            )}
            {renderPreview(preview)}
          </div>
        )}

        <footer className={styles.footer}>
          <p
            className={styles.saveState}
            aria-live="polite"
            title={`${MOD_KEY_LABEL}+S — сохранить, «/» — блоки`}
          >
            {saveState}
          </p>
          <Button
            className={styles.previewButton}
            aria-pressed={preview !== null}
            onClick={() =>
              setPreview((current) =>
                current === null ? state.getContent() : null,
              )
            }
          >
            {preview === null ? 'Предпросмотр' : 'Вернуться к правке'}
          </Button>
        </footer>

        <Dialog
          open={state.blocker.state === 'blocked'}
          onClose={() => state.blocker.reset?.()}
          title="Уйти без сохранения?"
          description="Несохранённые изменения останутся в этом браузере — их можно будет восстановить, открыв редактор снова."
        >
          <DialogActions>
            <Button onClick={() => state.blocker.reset?.()}>Остаться</Button>
            <Button variant="danger" onClick={() => state.blocker.proceed?.()}>
              Уйти
            </Button>
          </DialogActions>
        </Dialog>
      </div>
    </>
  );
}
