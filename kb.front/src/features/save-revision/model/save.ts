import {
  refreshSpaceArticles,
  setArticleDetail,
  type ArticleDetail,
} from '@entities/article';
import {
  refreshNavigation,
  type CollectionPlacement,
} from '@entities/collection';
import { ApiError, kbApi } from '@shared/api';
import { slugify } from '@shared/lib/slug';

export interface ArticleDraft {
  title: string;
  content: string;
  summary: string | null;
}

/** Кто-то сохранил новую редакцию, пока пользователь редактировал свою копию. */
export class RevisionConflictError extends Error {
  constructor() {
    super('Статья изменилась, пока вы её редактировали');
    this.name = 'RevisionConflictError';
  }
}

function afterSave(detail: ArticleDetail) {
  setArticleDetail(detail, 'draft');
  // Заголовок и статус видны в навигации и списках
  void refreshNavigation(detail.article.spaceId);
  void refreshSpaceArticles(detail.article.spaceId);
}

/** Создаёт черновик статьи с первой редакцией и, если указано, кладёт его в коллекцию. */
export async function createArticle(
  spaceId: string,
  draft: ArticleDraft,
  collectionId?: string | null,
): Promise<ArticleDetail> {
  const create = (slug: string) =>
    kbApi.post<ArticleDetail>(`/api/user/v1/spaces/${spaceId}/articles`, {
      body: { slug, ...draft, summary: draft.summary || undefined },
    });

  const slug = slugify(draft.title) || 'article';
  const detail = await create(slug).catch((error: unknown) => {
    // Slug уже занят в пространстве: адреса статей строятся по id, поэтому просто добавляем суффикс
    if (error instanceof ApiError && error.status === 409)
      return create(`${slug}-${Date.now().toString(36)}`);
    throw error;
  });

  if (collectionId) {
    await kbApi
      .post<CollectionPlacement>(
        `/api/user/v1/collections/${collectionId}/placements`,
        {
          body: {
            target: { type: 'article', id: detail.article.id },
            position: {},
          },
        },
      )
      // Статья уже создана: без размещения она просто окажется «вне коллекций»
      .catch(() => null);
  }

  afterSave(detail);
  return detail;
}

/**
 * Сохраняет новую редакцию. `baseRevisionId` — редакция, которую открыл редактор:
 * если с тех пор появилась другая, backend вернёт 409, и текст пользователя не потеряется.
 */
export async function saveRevision(
  articleId: string,
  baseRevisionId: string,
  draft: ArticleDraft & { changeNote?: string | null },
): Promise<ArticleDetail> {
  try {
    const detail = await kbApi.post<ArticleDetail>(
      `/api/user/v1/articles/${articleId}/revisions`,
      {
        body: {
          expectedRevisionId: baseRevisionId,
          title: draft.title,
          content: draft.content,
          summary: draft.summary || undefined,
          changeNote: draft.changeNote || undefined,
        },
      },
    );
    afterSave(detail);
    return detail;
  } catch (error) {
    if (error instanceof ApiError && error.status === 409)
      throw new RevisionConflictError();
    throw error;
  }
}

/** Актуальная редакторская версия — чтобы сохранить поверх после конфликта. */
export function loadLatestDraft(articleId: string): Promise<ArticleDetail> {
  return kbApi.get<ArticleDetail>(`/api/user/v1/articles/${articleId}/draft`);
}
