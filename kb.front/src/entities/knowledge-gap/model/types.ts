export type GapKind =
  | 'needs_triage'
  | 'missing_content'
  | 'incomplete_content'
  | 'outdated_content'
  | 'conflicting_content'
  | 'discoverability';

export type GapStatus = 'open' | 'in_progress' | 'resolved' | 'dismissed';

export interface KnowledgeGap {
  id: string;
  organizationId: string;
  groupingKey: string;
  title: string;
  spaceId: string | null;
  kind: GapKind;
  status: GapStatus;
  ownerId: string | null;
  relatedArticleId: string | null;
  resolutionNote: string | null;
  rationale: string | null;
  signalCount: number;
}

export const GAP_KIND_LABELS: Record<GapKind, string> = {
  needs_triage: 'Требует разбора',
  missing_content: 'Нет материала',
  incomplete_content: 'Неполная инструкция',
  outdated_content: 'Устаревший материал',
  conflicting_content: 'Противоречия',
  discoverability: 'Проблема находимости',
};

export const GAP_STATUS_LABELS: Record<GapStatus, string> = {
  open: 'Ожидает разбора',
  in_progress: 'В работе',
  resolved: 'Решено',
  dismissed: 'Отклонено',
};

export const GAP_KIND_ACTION: Record<GapKind, string> = {
  needs_triage: 'Классифицировать проблему',
  missing_content: 'Создать недостающую статью',
  incomplete_content: 'Дополнить существующую статью',
  outdated_content: 'Обновить устаревшие сведения',
  conflicting_content: 'Согласовать противоречивые материалы',
  discoverability: 'Улучшить заголовок и поисковые термины',
};
