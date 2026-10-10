/** Адреса экранов приложения. Ссылки на статьи в Markdown строятся этими же функциями. */
export const routes = {
  home: () => '/',
  login: () => '/login',
  search: (query?: string) =>
    query
      ? `/search?${new URLSearchParams({ q: query }).toString()}`
      : '/search',
  space: (spaceId: string) => `/spaces/${spaceId}`,
  newArticle: (spaceId: string, collectionId?: string) =>
    `/spaces/${spaceId}/new${collectionId ? `?collection=${collectionId}` : ''}`,
  article: (articleId: string, anchor?: string | null) =>
    `/articles/${articleId}${anchor ? `#${anchor}` : ''}`,
  editArticle: (articleId: string) => `/articles/${articleId}/edit`,
  articleHistory: (articleId: string) => `/articles/${articleId}/history`,
};

const ARTICLE_PATH = /^\/articles\/([0-9a-f-]{36})\/?$/i;

/** Идентификатор статьи из внутренней ссылки (`/articles/<id>` или полный URL приложения). */
export function articleIdFromHref(href: string): string | null {
  try {
    const url = new URL(href, window.location.origin);
    if (url.origin !== window.location.origin) return null;
    return ARTICLE_PATH.exec(url.pathname)?.[1] ?? null;
  } catch {
    return null;
  }
}
