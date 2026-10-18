import { useEffect } from 'react';
import { loadArticle, useArticleEntry } from '@entities/article';

export type View = 'published' | 'draft';

/**
 * Читатель видит опубликованную редакцию. Черновик загружается, только если
 * опубликованной нет или редактор явно переключился на него.
 */
export function useArticleForReading(articleId: string, view: View) {
  const published = useArticleEntry(articleId, 'published');
  const draft = useArticleEntry(articleId, 'draft');

  useEffect(() => {
    void loadArticle(articleId, 'published');
  }, [articleId]);

  const publishedMissing = published?.status === 'error';
  const wantsDraft = view === 'draft' || publishedMissing;

  useEffect(() => {
    if (wantsDraft) void loadArticle(articleId, 'draft');
  }, [articleId, wantsDraft]);

  if (!published || published.status === 'loading')
    return { status: 'loading' as const };

  if (!publishedMissing && view === 'published' && published.data)
    return {
      status: 'ready' as const,
      detail: published.data,
      version: 'published' as const,
      published: published.data,
    };

  if (!draft || draft.status === 'loading')
    return { status: 'loading' as const };
  if (draft.data)
    return {
      status: 'ready' as const,
      detail: draft.data,
      version: 'draft' as const,
      published: published.data,
    };

  return { status: 'missing' as const };
}
