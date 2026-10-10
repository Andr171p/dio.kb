import {
  setArticleDetail,
  type Article,
  type ArticleDetail,
} from '@entities/article';
import { refreshNavigation } from '@entities/collection';
import { ApiError, describeError, kbApi } from '@shared/api';
import { toast } from '@shared/ui/toast';

/**
 * Восстановление создаёт новую редакцию с содержимым исторической — история не переписывается.
 * Опубликованная версия не меняется до явной публикации.
 */
export async function restoreRevision(
  article: Pick<Article, 'id' | 'spaceId' | 'currentRevisionId'>,
  revision: { id: string; number: number },
): Promise<ArticleDetail | null> {
  try {
    const detail = await kbApi.post<ArticleDetail>(
      `/api/user/v1/articles/${article.id}/revisions/${revision.id}/restore`,
      {
        body: {
          expectedRevisionId: article.currentRevisionId,
          changeNote: `Восстановлена редакция ${revision.number}`,
        },
      },
    );
    setArticleDetail(detail, 'draft');
    void refreshNavigation(article.spaceId);
    toast.success(
      `Редакция ${revision.number} восстановлена как новая — ${detail.revision.number}. Опубликуйте её, чтобы увидели читатели.`,
    );
    return detail;
  } catch (error) {
    toast.error(
      error instanceof ApiError && error.status === 409
        ? 'Пока вы смотрели историю, появилась новая редакция. Обновите страницу.'
        : describeError(error),
    );
    return null;
  }
}
