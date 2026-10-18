import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { registerStoreReset } from '@shared/lib/store-reset';
import { USER_STORAGE_PREFIX } from '@shared/lib/user-storage';

export interface RecentArticle {
  id: string;
  title: string;
  spaceId: string;
  visitedAt: string;
}

interface RecentState {
  items: RecentArticle[];
}

const LIMIT = 8;

/** Недавно открытые статьи — только удобство в этом браузере, очищается при выходе. */
export const useRecentArticles = create<RecentState>()(
  persist(() => ({ items: [] as RecentArticle[] }), {
    name: `${USER_STORAGE_PREFIX}recent-articles`,
  }),
);

registerStoreReset(() => useRecentArticles.setState({ items: [] }));

export function rememberArticleVisit(
  article: Omit<RecentArticle, 'visitedAt'>,
) {
  useRecentArticles.setState(({ items }) => ({
    items: [
      { ...article, visitedAt: new Date().toISOString() },
      ...items.filter((item) => item.id !== article.id),
    ].slice(0, LIMIT),
  }));
}

/** Статья стала недоступной или удалена — убираем её из недавних. */
export function forgetArticleVisit(articleId: string) {
  useRecentArticles.setState(({ items }) => ({
    items: items.filter((item) => item.id !== articleId),
  }));
}
