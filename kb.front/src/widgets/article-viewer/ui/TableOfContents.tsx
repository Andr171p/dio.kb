import clsx from 'clsx';
import { ChevronDown } from 'lucide-react';
import { Menu, MenuItem } from '@shared/ui/menu';
import { usePopover } from '@shared/ui/popover';
import type { HeadingItem } from '../model/headings';
import styles from './TableOfContents.module.scss';

interface TableOfContentsProps {
  headings: HeadingItem[];
  active: string | null;
}

/** Оглавление в правой колонке: «В этой статье». */
export function TableOfContents({ headings, active }: TableOfContentsProps) {
  if (headings.length < 2) return null;

  return (
    <nav className={styles.toc} aria-label="Содержание статьи">
      <p className={styles.title}>В этой статье</p>
      <ul className={styles.list}>
        {headings.map((heading) => (
          <li key={heading.id}>
            <a
              href={`#${heading.id}`}
              className={clsx(
                styles.link,
                heading.level === 3 && styles.nested,
                active === heading.id && styles.active,
              )}
              aria-current={active === heading.id ? 'location' : undefined}
            >
              {heading.text}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}

/** Оглавление на узком экране: кнопка «Оглавление · текущий раздел». */
export function TableOfContentsMenu({
  headings,
  active,
}: TableOfContentsProps) {
  const { triggerProps, popoverProps } = usePopover();
  if (headings.length < 2) return null;

  const current = headings.find((heading) => heading.id === active);

  return (
    <>
      <button type="button" className={styles.menuTrigger} {...triggerProps}>
        <span className={styles.menuLabel}>
          Оглавление{current ? ` · ${current.text}` : ''}
        </span>
        <ChevronDown size={16} aria-hidden />
      </button>
      <Menu {...popoverProps} placement="bottom-start" className={styles.menu}>
        {headings.map((heading) => (
          <MenuItem
            key={heading.id}
            selected={heading.id === active}
            onSelect={() => {
              document
                .getElementById(heading.id)
                ?.scrollIntoView({ block: 'start' });
              history.replaceState(null, '', `#${heading.id}`);
            }}
          >
            {heading.text}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}
