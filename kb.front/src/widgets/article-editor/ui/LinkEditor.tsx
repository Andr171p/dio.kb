import type { Editor } from '@tiptap/react';
import clsx from 'clsx';
import { Check, FileText, Link2Off } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useSpaceArticles } from '@entities/article';
import { routes } from '@shared/config/routes';
import styles from './EditorToolbar.module.scss';

const SUGGESTION_LIMIT = 5;

function looksLikeUrl(value: string): boolean {
  return (
    /^(https?:\/\/|mailto:|tel:|\/|#)/i.test(value) ||
    /^[\w-]+\.[a-z]{2,}/i.test(value)
  );
}

function normalizeHref(value: string): string {
  if (/^(https?:\/\/|mailto:|tel:|\/|#)/i.test(value)) return value;
  return `https://${value}`;
}

interface LinkEditorProps {
  editor: Editor;
  onDone: () => void;
}

/**
 * Ввод ссылки: URL или название статьи базы знаний —
 * внутренние ссылки сохраняются как `/articles/<id>` и показываются с превью.
 */
export function LinkEditor({ editor, onDone }: LinkEditorProps) {
  const current =
    (editor.getAttributes('link').href as string | undefined) ?? '';
  const [value, setValue] = useState(current);
  const [active, setActive] = useState(0);
  const bySpace = useSpaceArticles((state) => state.bySpace);

  const suggestions = useMemo(() => {
    const query = value.trim().toLocaleLowerCase('ru');
    if (!query || looksLikeUrl(query)) return [];
    return Object.values(bySpace)
      .flatMap((entry) => entry?.items ?? [])
      .filter(
        (article) =>
          article.status !== 'archived' &&
          article.title.toLocaleLowerCase('ru').includes(query),
      )
      .slice(0, SUGGESTION_LIMIT);
  }, [bySpace, value]);

  const apply = (href: string) => {
    const chain = editor.chain().focus().extendMarkRange('link');
    if (href) chain.setLink({ href }).run();
    else chain.unsetLink().run();
    onDone();
  };

  return (
    <div className={styles.linkEditor}>
      <form
        className={styles.linkForm}
        onSubmit={(event) => {
          event.preventDefault();
          const suggestion = suggestions[active];
          if (suggestion) apply(routes.article(suggestion.id));
          else apply(value.trim() ? normalizeHref(value.trim()) : '');
        }}
      >
        <input
          className={styles.linkInput}
          value={value}
          placeholder="Вставьте ссылку или найдите статью"
          aria-label="Адрес ссылки"
          autoFocus
          onChange={(event) => {
            setValue(event.target.value);
            setActive(0);
          }}
          onKeyDown={(event) => {
            if (event.key === 'Escape') {
              event.preventDefault();
              onDone();
              editor.commands.focus();
            }
            if (suggestions.length === 0) return;
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
              event.preventDefault();
              const delta = event.key === 'ArrowDown' ? 1 : -1;
              setActive(
                (index) =>
                  (index + delta + suggestions.length) % suggestions.length,
              );
            }
          }}
        />
        <button
          type="submit"
          className={styles.tool}
          aria-label="Применить ссылку"
        >
          <Check size={15} aria-hidden />
        </button>
        {current && (
          <button
            type="button"
            className={styles.tool}
            aria-label="Убрать ссылку"
            onClick={() => apply('')}
          >
            <Link2Off size={15} aria-hidden />
          </button>
        )}
      </form>
      {suggestions.length > 0 && (
        <ul className={styles.suggestions} role="listbox" aria-label="Статьи">
          {suggestions.map((article, index) => (
            <li key={article.id}>
              <button
                type="button"
                role="option"
                aria-selected={index === active}
                className={clsx(
                  styles.suggestion,
                  index === active && styles.suggestionActive,
                )}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => apply(routes.article(article.id))}
              >
                <FileText size={14} aria-hidden />
                <span>{article.title}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
