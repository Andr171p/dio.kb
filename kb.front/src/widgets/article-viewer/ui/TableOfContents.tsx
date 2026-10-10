import clsx from 'clsx';
import { useEffect, useState, type RefObject } from 'react';
import styles from './TableOfContents.module.scss';

interface HeadingItem {
  id: string;
  text: string;
  level: number;
}

const SELECTOR = 'h2[id], h3[id]';

/** Заголовки берём из отрендеренной статьи — якоря гарантированно совпадают с адресами. */
function useHeadings(
  containerRef: RefObject<HTMLElement | null>,
  contentKey: string,
): HeadingItem[] {
  const [headings, setHeadings] = useState<HeadingItem[]>([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    setHeadings(
      [...container.querySelectorAll<HTMLElement>(SELECTOR)].map((element) => ({
        id: element.id,
        text: element.textContent?.trim() ?? '',
        level: Number(element.tagName.slice(1)),
      })),
    );
  }, [containerRef, contentKey]);

  return headings;
}

function useActiveHeading(headings: HeadingItem[]): string | null {
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    if (headings.length === 0) return;
    const visible = new Map<string, boolean>();

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) =>
          visible.set(entry.target.id, entry.isIntersecting),
        );
        const first = headings.find((heading) => visible.get(heading.id));
        if (first) setActive(first.id);
      },
      // Активен раздел, заголовок которого в верхней трети экрана
      { rootMargin: '-64px 0px -66% 0px' },
    );

    headings.forEach((heading) => {
      const element = document.getElementById(heading.id);
      if (element) observer.observe(element);
    });
    return () => observer.disconnect();
  }, [headings]);

  return active;
}

interface TableOfContentsProps {
  containerRef: RefObject<HTMLElement | null>;
  contentKey: string;
}

export function TableOfContents({
  containerRef,
  contentKey,
}: TableOfContentsProps) {
  const headings = useHeadings(containerRef, contentKey);
  const active = useActiveHeading(headings);

  if (headings.length < 2) return null;

  return (
    <nav className={styles.toc} aria-label="Содержание статьи">
      <p className={styles.title}>На этой странице</p>
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
