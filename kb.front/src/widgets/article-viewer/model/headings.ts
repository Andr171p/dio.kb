import { useEffect, useState, type RefObject } from 'react';

export interface HeadingItem {
  id: string;
  text: string;
  level: number;
}

const SELECTOR = 'h2[id], h3[id]';

/** Заголовки берём из отрендеренной статьи — якоря гарантированно совпадают с адресами. */
export function useHeadings(
  containerRef: RefObject<HTMLElement | null>,
  contentKey: string,
  leading: HeadingItem[] = [],
): HeadingItem[] {
  const [headings, setHeadings] = useState<HeadingItem[]>([]);
  const leadingKey = leading.map((item) => item.id).join(',');

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    setHeadings([
      ...leading,
      ...[...container.querySelectorAll<HTMLElement>(SELECTOR)].map(
        (element) => ({
          id: element.id,
          text: element.textContent?.trim() ?? '',
          level: Number(element.tagName.slice(1)),
        }),
      ),
    ]);
    // leading описан ключом: массив пересоздаётся на каждом рендере
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [containerRef, contentKey, leadingKey]);

  return headings;
}

export function useActiveHeading(headings: HeadingItem[]): string | null {
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

  return active ?? headings[0]?.id ?? null;
}
