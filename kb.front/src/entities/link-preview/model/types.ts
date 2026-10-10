import type { ArticleStatus } from '@entities/article';

export type LinkPreview =
  | {
      kind: 'article';
      href: string;
      articleId: string;
      title: string;
      summary: string | null;
      status: ArticleStatus;
      updatedAt: string;
    }
  | {
      kind: 'ticket';
      href: string;
      number: string;
      title: string;
      status: string;
      priority: string | null;
    }
  | {
      kind: 'external';
      href: string;
      title: string | null;
      description: string | null;
      imageUrl: string | null;
      siteName: string | null;
      faviconUrl: string | null;
    };
