import { Link2 } from 'lucide-react';
import { Link } from 'react-router';
import { routes } from '@shared/config/routes';
import type { AnswerSource } from '../model/types';
import styles from './AnswerCitation.module.scss';

interface AnswerCitationProps {
  index: number;
  source: AnswerSource | undefined;
  onPreview?: (source: AnswerSource) => void;
}

/** Компактная ссылка на источник — без красного акцента. */
export function AnswerCitation({
  index,
  source,
  onPreview,
}: AnswerCitationProps) {
  if (!source) {
    return <span className={styles.unknown}>[{index}]</span>;
  }

  if (onPreview) {
    return (
      <button
        type="button"
        className={styles.citation}
        title={source.title}
        aria-label={`Источник ${index}: ${source.title}`}
        onClick={() => onPreview(source)}
      >
        <Link2 size={10} aria-hidden />
      </button>
    );
  }

  return (
    <Link
      to={routes.article(source.articleId, source.anchor)}
      className={styles.citation}
      title={source.title}
      aria-label={`Источник ${index}: ${source.title}`}
    >
      <Link2 size={10} aria-hidden />
    </Link>
  );
}
