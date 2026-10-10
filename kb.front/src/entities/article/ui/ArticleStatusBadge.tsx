import { Badge } from '@shared/ui/badge';
import { STATUS_LABELS, type ArticleStatus } from '../model/types';

const TONES = {
  draft: 'warning',
  published: 'success',
  archived: 'neutral',
} as const;

export function ArticleStatusBadge({ status }: { status: ArticleStatus }) {
  return <Badge tone={TONES[status]}>{STATUS_LABELS[status]}</Badge>;
}
