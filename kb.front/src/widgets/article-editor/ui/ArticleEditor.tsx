import DragHandle from '@tiptap/extension-drag-handle-react';
import { EditorContent, useEditorState } from '@tiptap/react';
import clsx from 'clsx';
import {
  ChevronDown,
  CircleAlert,
  Copy,
  GripVertical,
  History,
  RotateCcw,
  Save,
  Send,
} from 'lucide-react';
import { useState, type ReactNode } from 'react';
import { hasPermission, type Permission } from '@entities/access-grant';
import type { ArticleDetail } from '@entities/article';
import { routes } from '@shared/config/routes';
import { formatRelative } from '@shared/lib/format';
import { MOD_KEY_LABEL, useCopyToClipboard } from '@shared/lib/hooks';
import { Button, ButtonLink } from '@shared/ui/button';
import { Callout } from '@shared/ui/callout';
import { Dialog, DialogActions } from '@shared/ui/dialog';
import { TextAreaField } from '@shared/ui/field';
import { Popover, usePopover } from '@shared/ui/popover';
import { toast } from '@shared/ui/toast';
import { Topbar } from '@shared/ui/topbar';
import {
  useArticleEditor,
  type EditorTarget,
} from '../model/use-article-editor';
import { SelectionToolbar, TableToolbar } from './EditorToolbar';
import styles from './ArticleEditor.module.scss';

interface ArticleEditorProps {
  target: EditorTarget;
  /** Права в пространстве (для новой статьи) или на статью */
  permissions: Permission[];
  topbarStart: ReactNode;
  onCreated: (detail: ArticleDetail) => void;
  onPublished: (detail: ArticleDetail) => void;
  onClose: () => void;
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
        size="sm"
        icon={Save}
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
        <ChevronDown size={14} aria-hidden />
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
          <Button type="submit" variant="primary" size="sm" icon={Save}>
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
  topbarStart,
  onCreated,
  onPublished,
  onClose,
}: ArticleEditorProps) {
  const state = useArticleEditor(target, { onCreated, onPublished });
  const { editor, detail, dirty, status } = state;
  const { copy } = useCopyToClipboard();
  const canPublish = hasPermission(permissions, 'PUBLISH');

  const stats = useEditorState({
    editor,
    selector: ({ editor: current }) => ({
      words:
        (current?.storage.characterCount.words() as number | undefined) ?? 0,
    }),
  });

  const minutes = Math.max(1, Math.round(stats.words / 180));

  return (
    <>
      <Topbar
        start={topbarStart}
        end={
          <>
            <span
              className={clsx(styles.saveState, dirty && styles.saveStateDirty)}
              aria-live="polite"
            >
              {dirty ? 'Не сохранено' : detail ? 'Сохранено' : ''}
            </span>
            {detail && (
              <ButtonLink
                to={routes.articleHistory(detail.article.id)}
                variant="ghost"
                size="sm"
                icon={History}
                className={styles.hideMobile}
              >
                История
              </ButtonLink>
            )}
            <Button variant="ghost" size="sm" onClick={onClose}>
              {detail ? 'Готово' : 'Отмена'}
            </Button>
            <SaveButton
              dirty={dirty || !detail}
              saving={status === 'saving'}
              onSave={(note) => void state.save(note)}
            />
            {canPublish && (
              <Button
                variant="primary"
                size="sm"
                icon={Send}
                loading={status === 'publishing'}
                disabled={status !== 'idle'}
                onClick={() => void state.publish()}
              >
                Опубликовать
              </Button>
            )}
          </>
        }
      />

      <div className={styles.page}>
        {state.conflict && (
          <Callout
            icon={CircleAlert}
            tone="warning"
            title="Статья изменилась, пока вы её редактировали"
            actions={
              <>
                <Button
                  size="sm"
                  icon={Copy}
                  onClick={() =>
                    void copy(state.getContent()).then(() =>
                      toast.success('Ваш текст скопирован в буфер обмена'),
                    )
                  }
                >
                  Скопировать мой текст
                </Button>
                {detail && (
                  <ButtonLink
                    size="sm"
                    to={routes.articleHistory(detail.article.id)}
                    target="_blank"
                    icon={History}
                  >
                    Открыть историю
                  </ButtonLink>
                )}
                <Button
                  size="sm"
                  variant="primary"
                  loading={status === 'saving'}
                  onClick={() => void state.overwrite()}
                >
                  Сохранить поверх
                </Button>
              </>
            }
          >
            Кто-то сохранил новую редакцию. Ваш текст остался в редакторе —
            сравните версии в истории или сохраните свою поверх: предыдущая
            редакция останется в истории.
          </Callout>
        )}

        {state.restorable && (
          <Callout
            icon={RotateCcw}
            tone="info"
            title="Найдены несохранённые изменения"
            actions={
              <>
                <Button size="sm" onClick={state.discardRestorable}>
                  Удалить
                </Button>
                <Button size="sm" variant="primary" onClick={state.restore}>
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
        <textarea
          className={styles.summary}
          value={state.summary}
          rows={1}
          placeholder="Краткое описание — показывается в поиске и превью ссылок"
          aria-label="Краткое описание"
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
              <DragHandle editor={editor} className={styles.dragHandle}>
                <GripVertical size={14} aria-hidden />
              </DragHandle>
              <SelectionToolbar editor={editor} />
              <TableToolbar editor={editor} />
            </>
          )}
          <EditorContent editor={editor} className={styles.content} />
        </div>
      </div>

      <footer
        className={styles.footer}
        title={`${MOD_KEY_LABEL}+S — сохранить, «/» — блоки`}
      >
        {stats.words} слов · ~{minutes} мин
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
    </>
  );
}
