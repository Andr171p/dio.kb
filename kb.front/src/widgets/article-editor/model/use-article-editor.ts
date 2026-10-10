import { useEditor, type Editor } from '@tiptap/react';
import {
  useCallback,
  useEffect,
  useEffectEvent,
  useMemo,
  useRef,
  useState,
} from 'react';
import { useBlocker } from 'react-router';
import type { ArticleDetail } from '@entities/article';
import { useCurrentUser } from '@entities/session';
import { publishArticle } from '@features/article-lifecycle';
import {
  createArticle,
  loadLatestDraft,
  RevisionConflictError,
  saveRevision,
} from '@features/save-revision';
import { describeError, uploadMedia } from '@shared/api';
import { toast } from '@shared/ui/toast';
import { createExtensions } from '../lib/extensions';
import { normalizeMarkdown } from '../lib/markdown';
import { insertImages, type MediaUploadOptions } from '../lib/media-upload';
import {
  clearLocalDraft,
  readLocalDraft,
  writeLocalDraft,
  type LocalDraft,
} from './local-draft';

export type EditorTarget =
  | { kind: 'edit'; detail: ArticleDetail }
  | { kind: 'new'; spaceId: string; collectionId: string | null };

interface Baseline {
  title: string;
  summary: string;
  /** Markdown после прохода через редактор — сравниваем с ним, а не с исходным текстом */
  content: string;
}

const LOCAL_DRAFT_DELAY_MS = 800;
const DIRTY_CHECK_DELAY_MS = 250;

function pickImage(insert: (files: File[]) => void) {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.multiple = true;
  input.onchange = () => insert([...(input.files ?? [])]);
  input.click();
}

export function useArticleEditor(
  target: EditorTarget,
  {
    onCreated,
    onPublished,
  }: {
    onCreated: (detail: ArticleDetail) => void;
    onPublished: (detail: ArticleDetail) => void;
  },
) {
  const user = useCurrentUser();
  const userId = user?.id ?? 'anonymous';
  const draftKey =
    target.kind === 'edit' ? target.detail.article.id : `new.${target.spaceId}`;
  const initial = target.kind === 'edit' ? target.detail.revision : null;

  const [detail, setDetail] = useState<ArticleDetail | null>(
    target.kind === 'edit' ? target.detail : null,
  );
  const [title, setTitle] = useState(initial?.title ?? '');
  const [summary, setSummary] = useState(initial?.summary ?? '');
  const [contentDirty, setContentDirty] = useState(false);
  const [status, setStatus] = useState<'idle' | 'saving' | 'publishing'>(
    'idle',
  );
  const [conflict, setConflict] = useState(false);
  const [restorable, setRestorable] = useState<LocalDraft | null>(() => {
    const saved = readLocalDraft(userId, draftKey);
    return saved && saved.content.trim() ? saved : null;
  });

  const [baseline, setBaseline] = useState<Baseline>({
    title: initial?.title ?? '',
    summary: initial?.summary ?? '',
    content: '',
  });
  const editorRef = useRef<Editor | null>(null);

  const uploadOptions = useMemo<MediaUploadOptions>(
    () => ({
      upload: (file) => uploadMedia(file, { type: 'user', id: userId }),
      onError: (error) =>
        toast.error(`Изображение не загружено: ${describeError(error)}`),
    }),
    [userId],
  );

  const extensions = useMemo(
    () =>
      createExtensions({
        ...uploadOptions,
        pickImage,
        insertImages: (files) => {
          if (editorRef.current)
            insertImages(editorRef.current, files, uploadOptions);
        },
      }),
    [uploadOptions],
  );

  const editor = useEditor(
    {
      extensions,
      content: initial?.content ?? '',
      contentType: 'markdown',
      immediatelyRender: true,
      shouldRerenderOnTransaction: false,
      editorProps: {
        attributes: { 'aria-label': 'Текст статьи', spellcheck: 'true' },
      },
      onCreate: ({ editor: created }) => {
        editorRef.current = created;
        const content = normalizeMarkdown(created.getMarkdown());
        setBaseline((current) => ({ ...current, content }));
      },
    },
    [extensions],
  );

  const getContent = useCallback(
    () => (editor ? normalizeMarkdown(editor.getMarkdown()) : ''),
    [editor],
  );

  // Изменения текста: сразу помечаем, а точное сравнение (с учётом отмены) — с задержкой
  useEffect(() => {
    if (!editor) return;
    let timer: ReturnType<typeof setTimeout>;
    const onUpdate = () => {
      setContentDirty(true);
      clearTimeout(timer);
      timer = setTimeout(
        () => setContentDirty(getContent() !== baseline.content),
        DIRTY_CHECK_DELAY_MS,
      );
    };
    editor.on('update', onUpdate);
    return () => {
      clearTimeout(timer);
      editor.off('update', onUpdate);
    };
  }, [editor, getContent, baseline.content]);

  const dirty =
    contentDirty ||
    title.trim() !== baseline.title ||
    summary.trim() !== baseline.summary;

  // Страховочная копия в браузере, пока есть несохранённые изменения
  useEffect(() => {
    if (!dirty || restorable) return;
    const timer = setTimeout(
      () =>
        writeLocalDraft(userId, draftKey, {
          title,
          summary,
          content: getContent(),
          baseRevisionId: detail?.revision.id ?? null,
        }),
      LOCAL_DRAFT_DELAY_MS,
    );
    return () => clearTimeout(timer);
  }, [
    dirty,
    restorable,
    userId,
    draftKey,
    title,
    summary,
    contentDirty,
    getContent,
    detail,
  ]);

  useEffect(() => {
    if (!dirty) return;
    const onBeforeUnload = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [dirty]);

  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      dirty &&
      status === 'idle' &&
      currentLocation.pathname !== nextLocation.pathname,
  );

  const markSaved = (saved: ArticleDetail | null, content: string) => {
    setBaseline({ title: title.trim(), summary: summary.trim(), content });
    setTitle((value) => value.trim());
    setSummary((value) => value.trim());
    setContentDirty(false);
    setConflict(false);
    if (saved) setDetail(saved);
    clearLocalDraft(userId, draftKey);
  };

  const validate = (content: string): boolean => {
    if (!title.trim()) {
      toast.error('Добавьте заголовок статьи');
      document.getElementById('article-title')?.focus();
      return false;
    }
    if (!content.trim()) {
      toast.error('Добавьте текст статьи');
      editor?.commands.focus();
      return false;
    }
    return true;
  };

  const save = async (
    changeNote?: string | null,
  ): Promise<ArticleDetail | null> => {
    if (status !== 'idle') return null;
    const content = getContent();
    if (!validate(content)) return null;

    if (!dirty && detail) return detail;

    setStatus('saving');
    try {
      const draft = {
        title: title.trim(),
        summary: summary.trim() || null,
        content,
      };
      if (!detail && target.kind === 'new') {
        const created = await createArticle(
          target.spaceId,
          draft,
          target.collectionId,
        );
        markSaved(created, content);
        toast.success('Черновик создан');
        onCreated(created);
        return created;
      }
      if (!detail) return null;

      const saved = await saveRevision(detail.article.id, detail.revision.id, {
        ...draft,
        changeNote,
      });
      markSaved(saved, content);
      toast.success(`Сохранено · редакция ${saved.revision.number}`);
      return saved;
    } catch (error) {
      if (error instanceof RevisionConflictError) setConflict(true);
      else toast.error(describeError(error));
      return null;
    } finally {
      setStatus('idle');
    }
  };

  /** После конфликта: новая редакция поверх актуальной. История сохранит обе версии. */
  const overwrite = async () => {
    if (!detail) return;
    setStatus('saving');
    try {
      const latest = await loadLatestDraft(detail.article.id);
      setDetail(latest);
      const content = getContent();
      const saved = await saveRevision(detail.article.id, latest.revision.id, {
        title: title.trim(),
        summary: summary.trim() || null,
        content,
        changeNote: 'Сохранено поверх параллельных изменений',
      });
      markSaved(saved, content);
      toast.success(`Сохранено · редакция ${saved.revision.number}`);
    } catch (error) {
      toast.error(describeError(error));
    } finally {
      setStatus('idle');
    }
  };

  const publish = async () => {
    const saved = await save('Публикация');
    if (!saved) return;
    setStatus('publishing');
    try {
      if (await publishArticle(saved.article)) onPublished(saved);
    } finally {
      setStatus('idle');
    }
  };

  const restore = () => {
    if (!restorable || !editor) return;
    setTitle(restorable.title);
    setSummary(restorable.summary);
    editor.commands.setContent(restorable.content, {
      contentType: 'markdown',
      emitUpdate: true,
    });
    setRestorable(null);
  };

  const discardRestorable = () => {
    clearLocalDraft(userId, draftKey);
    setRestorable(null);
  };

  // Ctrl/⌘+S — быстрое сохранение без комментария
  const onSaveHotkey = useEffectEvent(() => void save());
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.code === 'KeyS' && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        onSaveHotkey();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return {
    editor,
    detail,
    title,
    setTitle,
    summary,
    setSummary,
    dirty,
    status,
    conflict,
    restorable,
    blocker,
    save,
    publish,
    overwrite,
    restore,
    discardRestorable,
    getContent,
  };
}
