import { useEffect } from 'react';
import { create } from 'zustand';
import { diosApi, kbApi } from '@shared/api';
import { env } from '@shared/config/env';
import { articleIdFromHref } from '@shared/config/routes';
import { registerStoreReset } from '@shared/lib/store-reset';
import type { ArticleDetail } from '@entities/article';
import type { LinkPreview } from './types';

interface LinkPreviewsState {
  /** null — превью недоступно (нет прав, страница не отвечает) */
  byHref: Record<string, LinkPreview | null | undefined>;
}

export const useLinkPreviews = create<LinkPreviewsState>()(() => ({
  byHref: {},
}));

registerStoreReset(() =>
  useLinkPreviews.setState(useLinkPreviews.getInitialState(), true),
);

interface TicketResponse {
  id: string;
  number: string;
  title: string;
  status: string;
  priority: string | null;
}

const DIOS_TICKET_PATH = /^\/tickets\/([^/?#]+)\/?$/;

function diosTicketNumber(href: string): string | null {
  try {
    const url = new URL(href);
    if (url.origin !== new URL(env.diosUrl).origin) return null;
    const number = DIOS_TICKET_PATH.exec(url.pathname)?.[1];
    return number && number !== 'new' ? decodeURIComponent(number) : null;
  } catch {
    return null;
  }
}

async function loadArticlePreview(
  href: string,
  articleId: string,
): Promise<LinkPreview> {
  // Только опубликованная редакция: ссылка в статье не должна раскрывать черновик
  const { article, revision } = await kbApi.get<ArticleDetail>(
    `/api/user/v1/articles/${articleId}`,
  );
  return {
    kind: 'article',
    href,
    articleId,
    title: revision.title,
    summary: revision.summary,
    status: article.status,
    updatedAt: article.updatedAt,
  };
}

async function loadTicketPreview(
  href: string,
  number: string,
): Promise<LinkPreview | null> {
  // DIOS адресует заявки номером, а API — id: находим заявку поиском по номеру
  const { items } = await diosApi.post<{ items: TicketResponse[] }>(
    '/api/v1/tickets/search',
    { query: { page: 1, size: 20 }, body: { search_query: number } },
  );
  const ticket = items.find((item) => item.number === number);
  return ticket
    ? {
        kind: 'ticket',
        href,
        number: ticket.number,
        title: ticket.title,
        status: ticket.status,
        priority: ticket.priority,
      }
    : null;
}

async function loadExternalPreview(href: string): Promise<LinkPreview | null> {
  const preview = await kbApi.get<{
    title: string | null;
    description: string | null;
    imageUrl: string | null;
    siteName: string | null;
    faviconUrl: string | null;
  }>('/api/user/v1/link-preview', { query: { url: href } });

  return preview.title || preview.description
    ? { kind: 'external', href, ...preview }
    : null;
}

function loadPreview(href: string): Promise<LinkPreview | null> {
  const articleId = articleIdFromHref(href);
  if (articleId) return loadArticlePreview(href, articleId);

  const ticketNumber = diosTicketNumber(href);
  if (ticketNumber) return loadTicketPreview(href, ticketNumber);

  if (/^https?:\/\//i.test(href)) return loadExternalPreview(href);
  return Promise.resolve(null);
}

const requested = new Set<string>();
registerStoreReset(() => requested.clear());

export function ensureLinkPreview(href: string) {
  if (requested.has(href)) return;
  requested.add(href);

  void loadPreview(href)
    .catch(() => null)
    .then((preview) =>
      useLinkPreviews.setState(({ byHref }) => ({
        byHref: { ...byHref, [href]: preview },
      })),
    );
}

/** Превью ссылки; загружается, только когда `enabled` (наведение, видимость карточки). */
export function useLinkPreview(
  href: string,
  enabled = true,
): LinkPreview | null | undefined {
  const preview = useLinkPreviews((state) => state.byHref[href]);

  useEffect(() => {
    if (enabled) ensureLinkPreview(href);
  }, [href, enabled]);

  return preview;
}
