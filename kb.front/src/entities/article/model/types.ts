import type { Permission } from '@entities/access-grant';

export type ArticleStatus = 'draft' | 'published' | 'archived';

export const STATUS_LABELS: Record<ArticleStatus, string> = {
  draft: 'Черновик',
  published: 'Опубликована',
  archived: 'В архиве',
};

/** Идентичность и жизненный цикл статьи. Содержимое — в неизменяемых редакциях. */
export interface Article {
  id: string;
  createdAt: string;
  updatedAt: string;
  spaceId: string;
  slug: string;
  status: ArticleStatus;
  /** Редакторская версия */
  currentRevisionId: string;
  /** Версия, которую видят читатели и поиск */
  publishedRevisionId: string | null;
  revisionNumber: number;
  hasUnpublishedChanges: boolean;
  authorId: string;
  publishedAt: string | null;
}

export interface ArticleRevisionSummary {
  id: string;
  createdAt: string;
  number: number;
  title: string;
  authorId: string;
  changeNote: string | null;
  restoredFromRevisionId: string | null;
}

export interface ArticleRevision extends ArticleRevisionSummary {
  articleId: string;
  previousRevisionId: string | null;
  summary: string | null;
  /** Markdown — канонический формат содержимого */
  content: string;
}

export interface ArticleDetail {
  article: Article;
  revision: ArticleRevision;
  permissions: Permission[];
}

export interface ArticleSummary {
  id: string;
  spaceId: string;
  slug: string;
  title: string;
  status: ArticleStatus;
  updatedAt: string;
  publishedAt: string | null;
}

/** Какая версия загружена: опубликованная (читатель) или текущая (редактор). */
export type ArticleVersion = 'published' | 'draft';
