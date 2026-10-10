import clsx from 'clsx';
import type { SuggestionProps } from '@tiptap/suggestion';
import {
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type Ref,
} from 'react';
import type { SlashItem } from '../lib/slash-commands';
import styles from './SlashMenu.module.scss';

export interface SlashMenuHandle {
  onKeyDown: (event: KeyboardEvent) => boolean;
}

type SlashMenuProps = SuggestionProps<SlashItem, SlashItem> & {
  ref?: Ref<SlashMenuHandle>;
};

export function SlashMenu({ items, command, ref }: SlashMenuProps) {
  const [active, setActive] = useState(0);
  const [prevItems, setPrevItems] = useState(items);
  const listRef = useRef<HTMLDivElement>(null);

  // Новый список — выделяем первый пункт
  if (prevItems !== items) {
    setPrevItems(items);
    setActive(0);
  }

  useEffect(() => {
    listRef.current
      ?.querySelector(`[data-index="${active}"]`)
      ?.scrollIntoView({ block: 'nearest' });
  }, [active]);

  useImperativeHandle(ref, () => ({
    onKeyDown: (event) => {
      if (items.length === 0) return false;
      if (event.key === 'ArrowDown') {
        setActive((index) => (index + 1) % items.length);
        return true;
      }
      if (event.key === 'ArrowUp') {
        setActive((index) => (index - 1 + items.length) % items.length);
        return true;
      }
      if (event.key === 'Enter' || event.key === 'Tab') {
        command(items[active]);
        return true;
      }
      return false;
    },
  }));

  if (items.length === 0)
    return (
      <div className={styles.menu}>
        <p className={styles.empty}>Нет подходящих блоков</p>
      </div>
    );

  return (
    <div
      className={styles.menu}
      ref={listRef}
      role="listbox"
      aria-label="Блоки"
    >
      {items.map((item, index) => {
        const Icon = item.icon;
        return (
          <button
            key={item.id}
            type="button"
            role="option"
            data-index={index}
            aria-selected={index === active}
            className={clsx(styles.item, index === active && styles.active)}
            onPointerMove={() => setActive(index)}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => command(item)}
          >
            <span className={styles.icon}>
              <Icon size={16} aria-hidden />
            </span>
            <span className={styles.text}>
              <span className={styles.title}>{item.title}</span>
              <span className={styles.description}>{item.description}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
