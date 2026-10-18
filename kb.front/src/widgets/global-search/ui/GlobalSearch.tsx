import clsx from 'clsx';
import {
  ArrowRight,
  Clock,
  CornerDownLeft,
  FilePlus,
  FileText,
  Moon,
  Search,
  TextSearch,
} from 'lucide-react';
import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import { useNavigate, useParams } from 'react-router';
import { hasPermission } from '@entities/access-grant';
import { useSpaces, type Space } from '@entities/space';
import { routes } from '@shared/config/routes';
import { toggleTheme } from '@shared/lib/theme';
import { Kbd } from '@shared/ui/kbd';
import { Spinner } from '@shared/ui/spinner';
import {
  useCommandResults,
  type CommandArticle,
} from '../model/use-command-results';
import styles from './GlobalSearch.module.scss';

interface GlobalSearchProps {
  open: boolean;
  onClose: () => void;
}

interface CommandItem {
  key: string;
  icon: typeof Search;
  title: ReactNode;
  meta?: ReactNode;
  snippet?: string;
  onSelect: () => void;
}

interface CommandGroup {
  label: string;
  items: CommandItem[];
  trailing?: ReactNode;
}

function spaceName(spaces: Space[], spaceId: string): string {
  return spaces.find((space) => space.id === spaceId)?.name ?? '';
}

/** Командная палитра: поиск статей по заголовку и содержимому, быстрые действия. */
export function GlobalSearch({ open, onClose }: GlobalSearchProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();
  const navigate = useNavigate();
  const { spaceId: currentSpaceId } = useParams();
  const spaces = useSpaces((state) => state.items);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const { recent, titleMatches, contentMatches, contentStatus } =
    useCommandResults(query, open);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      setQuery('');
      setActiveIndex(0);
      inputRef.current?.focus();
    }
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const go = (to: string) => {
    onClose();
    void navigate(to);
  };

  const groups = useMemo<CommandGroup[]>(() => {
    const articleItem = (
      prefix: string,
      article: CommandArticle,
    ): CommandItem => ({
      key: `${prefix}:${article.id}`,
      icon: FileText,
      title: article.title,
      meta: [spaceName(spaces, article.spaceId), ...(article.headingPath ?? [])]
        .filter(Boolean)
        .join(' › '),
      snippet: article.snippet,
      onSelect: () => go(routes.article(article.id, article.anchor)),
    });

    const trimmed = query.trim();
    const result: CommandGroup[] = [];

    if (recent.length > 0)
      result.push({
        label: 'Недавние',
        items: recent.map((article) => ({
          ...articleItem('recent', article),
          icon: Clock,
        })),
      });

    if (titleMatches.length > 0)
      result.push({
        label: 'Статьи',
        items: titleMatches.map((article) => articleItem('title', article)),
      });

    if (contentStatus !== 'idle')
      result.push({
        label: 'По содержимому',
        trailing: contentStatus === 'loading' && <Spinner size={12} />,
        items: contentMatches.map((article) => articleItem('content', article)),
      });

    const writableSpace =
      spaces.find(
        (space) =>
          space.id === currentSpaceId &&
          hasPermission(space.permissions, 'WRITE'),
      ) ?? spaces.find((space) => hasPermission(space.permissions, 'WRITE'));

    const actions: CommandItem[] = [];
    if (trimmed)
      actions.push({
        key: 'action:search',
        icon: TextSearch,
        title: (
          <>
            Искать «<span className={styles.query}>{trimmed}</span>» во всех
            статьях
          </>
        ),
        onSelect: () => go(routes.search(trimmed)),
      });
    else {
      if (writableSpace)
        actions.push({
          key: 'action:new-article',
          icon: FilePlus,
          title: 'Новая статья',
          meta: writableSpace.name,
          onSelect: () => go(routes.newArticle(writableSpace.id)),
        });
      actions.push(
        {
          key: 'action:search-page',
          icon: TextSearch,
          title: 'Поиск по содержимому',
          onSelect: () => go(routes.search()),
        },
        {
          key: 'action:theme',
          icon: Moon,
          title: 'Сменить тему',
          onSelect: () => {
            toggleTheme();
            onClose();
          },
        },
      );
    }
    result.push({ label: 'Действия', items: actions });

    return result;
    // go и onClose стабильны по смыслу: пересчитываем только по данным
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    query,
    recent,
    titleMatches,
    contentMatches,
    contentStatus,
    spaces,
    currentSpaceId,
  ]);

  const items = groups.flatMap((group) => group.items);
  const active = Math.min(activeIndex, Math.max(items.length - 1, 0));

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      const delta = event.key === 'ArrowDown' ? 1 : -1;
      setActiveIndex(
        (active + delta + items.length) % Math.max(items.length, 1),
      );
    } else if (event.key === 'Enter') {
      event.preventDefault();
      items[active]?.onSelect();
    }
  };

  useEffect(() => {
    document
      .getElementById(`${listId}-${active}`)
      ?.scrollIntoView({ block: 'nearest' });
  }, [active, listId]);

  let index = 0;

  return createPortal(
    <dialog
      ref={dialogRef}
      className={styles.dialog}
      aria-label="Поиск по базе знаний"
      onClose={onClose}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      {open && (
        <div className={styles.panel} onKeyDown={onKeyDown}>
          <div className={styles.inputRow}>
            <Search
              size={22}
              strokeWidth={1.6}
              className={styles.inputIcon}
              aria-hidden
            />
            <input
              ref={inputRef}
              className={styles.input}
              value={query}
              placeholder="Найти статью, раздел или действие…"
              role="combobox"
              aria-expanded
              aria-controls={listId}
              aria-activedescendant={
                items.length ? `${listId}-${active}` : undefined
              }
              aria-autocomplete="list"
              onChange={(event) => {
                setQuery(event.target.value);
                setActiveIndex(0);
              }}
            />
            <Kbd keys={['Esc']} />
          </div>

          <div id={listId} role="listbox" className={styles.results}>
            {groups.map((group) => (
              <section
                key={group.label}
                className={styles.group}
                aria-label={group.label}
              >
                <header className={styles.groupLabel}>
                  {group.label}
                  {group.trailing}
                </header>
                {group.items.length === 0 &&
                  group.label === 'По содержимому' && (
                    <p className={styles.empty}>
                      {contentStatus === 'loading'
                        ? 'Ищем по опубликованным статьям…'
                        : contentStatus === 'error'
                          ? 'Поиск по содержимому недоступен'
                          : 'Ничего не найдено'}
                    </p>
                  )}
                {group.items.map((item) => {
                  const itemIndex = index++;
                  const Icon = item.icon;
                  return (
                    <div
                      key={item.key}
                      id={`${listId}-${itemIndex}`}
                      role="option"
                      aria-selected={itemIndex === active}
                      className={clsx(
                        styles.item,
                        itemIndex === active && styles.active,
                      )}
                      onPointerMove={() => setActiveIndex(itemIndex)}
                      onClick={item.onSelect}
                    >
                      <Icon size={16} className={styles.itemIcon} aria-hidden />
                      <div className={styles.itemText}>
                        <span className={styles.itemTitle}>{item.title}</span>
                        {item.meta && (
                          <span className={styles.itemMeta}>{item.meta}</span>
                        )}
                        {item.snippet && (
                          <span className={styles.itemSnippet}>
                            {item.snippet}
                          </span>
                        )}
                      </div>
                      {itemIndex === active && (
                        <CornerDownLeft
                          size={14}
                          className={styles.enter}
                          aria-hidden
                        />
                      )}
                    </div>
                  );
                })}
              </section>
            ))}
          </div>

          <footer className={styles.footer}>
            <span>
              <Kbd keys={['↑', '↓']} /> выбор
            </span>
            <span>
              <Kbd keys={['Enter']} /> открыть
            </span>
            <span className={styles.footerHint}>
              <ArrowRight size={12} aria-hidden /> Поиск учитывает только
              опубликованные статьи, доступные вам
            </span>
          </footer>
        </div>
      )}
    </dialog>,
    document.body,
  );
}
