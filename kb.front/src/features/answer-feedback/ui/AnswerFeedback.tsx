import clsx from 'clsx';
import { Check, Copy, ThumbsDown, ThumbsUp } from 'lucide-react';
import { useState } from 'react';
import {
  putAnswerFeedback,
  type FeedbackReason,
} from '@entities/answer';
import { describeError } from '@shared/api';
import { useCopyToClipboard } from '@shared/lib/hooks';
import { Button } from '@shared/ui/button';
import { toast } from '@shared/ui/toast';
import styles from './AnswerFeedback.module.scss';

const REASONS: { value: FeedbackReason; label: string }[] = [
  { value: 'no_solution', label: 'Нет решения' },
  { value: 'incorrect', label: 'Неверно' },
  { value: 'incomplete', label: 'Неполно' },
  { value: 'outdated', label: 'Устарело' },
  { value: 'irrelevant_sources', label: 'Плохие источники' },
  { value: 'other', label: 'Другое' },
];

interface AnswerFeedbackProps {
  answerId: string;
  copyText?: string;
}

/** Ненавязчивая оценка справа: 👍 / 👎 / копировать. */
export function AnswerFeedback({ answerId, copyText }: AnswerFeedbackProps) {
  const [helpful, setHelpful] = useState<boolean | null>(null);
  const [reason, setReason] = useState<FeedbackReason | null>(null);
  const [comment, setComment] = useState('');
  const [showReasons, setShowReasons] = useState(false);
  const [saving, setSaving] = useState(false);
  const { copied, copy } = useCopyToClipboard();

  const save = async (next: {
    helpful: boolean;
    reason?: FeedbackReason | null;
    comment?: string;
  }) => {
    const previous = { helpful, reason, comment };
    setHelpful(next.helpful);
    setReason(next.reason ?? null);
    if (next.comment !== undefined) setComment(next.comment);
    setSaving(true);
    try {
      await putAnswerFeedback(answerId, {
        helpful: next.helpful,
        reason: next.helpful ? null : (next.reason ?? null),
        comment: next.helpful ? null : (next.comment || null),
      });
    } catch (error) {
      setHelpful(previous.helpful);
      setReason(previous.reason);
      setComment(previous.comment);
      toast.error(describeError(error));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.root}>
      <p className={styles.disclaimer}>
        Использует ИИ. Проверяйте ответ по источникам.
      </p>
      <div className={styles.actions}>
        <button
          type="button"
          className={clsx(styles.iconBtn, helpful === true && styles.active)}
          aria-label="Ответ полезен"
          aria-pressed={helpful === true}
          disabled={saving}
          onClick={() => {
            setShowReasons(false);
            void save({ helpful: true });
          }}
        >
          <ThumbsUp size={15} aria-hidden />
        </button>
        <button
          type="button"
          className={clsx(styles.iconBtn, helpful === false && styles.active)}
          aria-label="Ответ не полезен"
          aria-pressed={helpful === false}
          disabled={saving}
          onClick={() => {
            setShowReasons(true);
            if (helpful !== false) setHelpful(false);
          }}
        >
          <ThumbsDown size={15} aria-hidden />
        </button>
        {copyText && (
          <button
            type="button"
            className={styles.iconBtn}
            aria-label={copied ? 'Скопировано' : 'Копировать ответ'}
            onClick={() => void copy(copyText)}
          >
            {copied ? <Check size={15} aria-hidden /> : <Copy size={15} aria-hidden />}
          </button>
        )}
      </div>

      {showReasons && (
        <div className={styles.reasons}>
          <p className={styles.reasonsLabel}>Что не так? (необязательно)</p>
          <div className={styles.reasonList} role="group">
            {REASONS.map((item) => (
              <button
                key={item.value}
                type="button"
                className={clsx(
                  styles.reason,
                  reason === item.value && styles.reasonActive,
                )}
                aria-pressed={reason === item.value}
                onClick={() =>
                  void save({
                    helpful: false,
                    reason: item.value,
                    comment,
                  })
                }
              >
                {item.label}
              </button>
            ))}
          </div>
          <textarea
            className={styles.comment}
            rows={2}
            maxLength={1000}
            placeholder="Короткий комментарий"
            value={comment}
            onChange={(event) => setComment(event.target.value)}
          />
          <Button
            size="sm"
            loading={saving}
            onClick={() => void save({ helpful: false, reason, comment })}
          >
            Отправить оценку
          </Button>
        </div>
      )}
    </div>
  );
}
