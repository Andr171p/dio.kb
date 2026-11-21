import { Link2 } from 'lucide-react';
import { Link } from 'react-router';
import { routes } from '@shared/config/routes';
import type { AnswerSource } from '../model/types';
import styles from './AnswerCitation.module.scss';

interface AnswerCitationProps {
  index: number;
  source: AnswerSource | undefined;
}

/** Превью-ссылка на источник прямо в тексте ответа. */
export function AnswerCitation({ index, source }: AnswerCitationProps) {
  if (!source) {
    return <span className={styles.unknown}>[{index}]</span>;
  }

  return (
    <Link
      to={routes.article(source.articleId, source.anchor)}
      className={styles.citation}
      title={source.title}
      aria-label={`Источник ${index}: ${source.title}`}
    >
      <Link2 size={10} aria-hidden />
      <span className={styles.label}>{source.title}</span>
    </Link>
  );
}
