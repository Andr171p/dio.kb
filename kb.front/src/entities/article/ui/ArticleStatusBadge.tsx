import { Badge } from '@shared/ui/badge';
import { STATUS_LABELS, type ArticleStatus } from '../model/types';

const TONES = {
  draft: 'accent',
  published: 'neutral',
  archived: 'neutral',
} as const;

export function ArticleStatusBadge({
  status,
  size,
}: {
  status: ArticleStatus;
  size?: 'md' | 'sm';
}) {
  return (
    <Badge tone={TONES[status]} size={size}>
      {STATUS_LABELS[status]}
    </Badge>
  );
}
