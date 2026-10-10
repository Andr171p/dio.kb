import {
  invalidateArticle,
  loadArticle,
  refreshSpaceArticles,
  type Article,
} from '@entities/article';
import { refreshNavigation } from '@entities/collection';
import { ApiError, describeError, kbApi } from '@shared/api';
import { toast } from '@shared/ui/toast';

/** Статус статьи изменился: перечитываем её версии, дерево и списки пространства. */
export async function syncArticleState(
  article: Pick<Article, 'id' | 'spaceId'>,
) {
  invalidateArticle(article.id);
  await Promise.all([
    loadArticle(article.id, 'draft'),
    loadArticle(article.id, 'published'),
    refreshNavigation(article.spaceId),
    refreshSpaceArticles(article.spaceId),
  ]);
}

/**
 * Публикует текущую редакцию. `revisionId` защищает от публикации версии, которую
 * пользователь не видел: если кто-то успел сохранить новую, backend вернёт 409.
 */
export async function publishArticle(article: Article): Promise<boolean> {
  try {
    await kbApi.post<Article>(`/api/user/v1/articles/${article.id}/publish`, {
      body: { revisionId: article.currentRevisionId },
    });
    toast.success(
      'Статья опубликована. Поиск обновится через несколько секунд.',
    );
    return true;
  } catch (error) {
    toast.error(
      error instanceof ApiError && error.status === 409
        ? 'Пока вы смотрели статью, появилась новая редакция. Обновите страницу и проверьте изменения перед публикацией.'
        : describeError(error),
    );
    return false;
  } finally {
    await syncArticleState(article);
  }
}

export async function unpublishArticle(article: Article): Promise<void> {
  try {
    await kbApi.post<Article>(`/api/user/v1/articles/${article.id}/unpublish`);
    toast.success('Статья снята с публикации — читатели её больше не видят');
  } catch (error) {
    toast.error(describeError(error));
    throw error;
  } finally {
    await syncArticleState(article);
  }
}

/** Архивирование сразу снимает публикацию: статья пропадает у читателей и из поиска. */
export async function archiveArticle(article: Article): Promise<void> {
  try {
    await kbApi.delete(`/api/user/v1/articles/${article.id}`);
    toast.success('Статья перемещена в архив');
  } catch (error) {
    toast.error(describeError(error));
    throw error;
  } finally {
    await syncArticleState(article);
  }
}

/** Возвращает статью из архива черновиком: публикация — отдельное явное действие. */
export async function restoreArticle(article: Article): Promise<void> {
  try {
    await kbApi.post<Article>(`/api/user/v1/articles/${article.id}/restore`);
    toast.success('Статья восстановлена как черновик');
  } catch (error) {
    toast.error(describeError(error));
    throw error;
  } finally {
    await syncArticleState(article);
  }
}
