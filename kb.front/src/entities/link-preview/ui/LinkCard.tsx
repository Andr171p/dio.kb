import type { ComponentProps } from 'react';
import { Link } from 'react-router';
import { useLinkPreview } from '../model/link-previews-store';
import { LinkPreviewBody } from './LinkPreviewCard';
import styles from './LinkCard.module.scss';

interface LinkCardProps extends Omit<ComponentProps<'a'>, 'href' | 'children'> {
  href: string;
}

/** Карточка ссылки, стоящей отдельным абзацем. В Markdown это остаётся обычной ссылкой. */
export function LinkCard({ href, ...props }: LinkCardProps) {
  const preview = useLinkPreview(href);

  const body = <LinkPreviewBody href={href} preview={preview} />;

  // Ссылки приложения открываем роутером, без перезагрузки страницы
  return href.startsWith('/') ? (
    <Link to={href} className={styles.card}>
      {body}
    </Link>
  ) : (
    <a href={href} className={styles.card} {...props}>
      {body}
    </a>
  );
}
