import { useEffect, useMemo } from 'react';
import { useParams } from 'react-router';
import type { Resource } from '@entities/access-grant';
import { loadArticle, useArticleEntry } from '@entities/article';
import {
  flattenCollections,
  loadNavigation,
  useSpaceNavigation,
} from '@entities/collection';
import { isAdmin, useCurrentUser } from '@entities/session';
import { loadSpaces, useSpace } from '@entities/space';
import { AccessManager } from '@features/manage-access';
import { AppHeader } from '@widgets/app-shell';
import { routes } from '@shared/config/routes';
import type { Crumb } from '@shared/ui/breadcrumbs';
import { ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Skeleton } from '@shared/ui/skeleton';
import styles from './AccessPage.module.scss';

const TITLES: Record<Resource['type'], string> = {
  space: 'Доступ к пространству',
  collection: 'Доступ к коллекции',
  article: 'Доступ к статье',
};

/** Название статьи: опубликованная редакция, а если её нет — текущая. */
function useArticleTitle(articleId: string | undefined) {
  const published = useArticleEntry(articleId, 'published');
  const draft = useArticleEntry(articleId, 'draft');
  const needsDraft = published?.status === 'error';

  useEffect(() => {
    if (articleId) void loadArticle(articleId, 'published');
  }, [articleId]);

  useEffect(() => {
    if (articleId && needsDraft) void loadArticle(articleId, 'draft');
  }, [articleId, needsDraft]);

  const detail = published?.data ?? draft?.data;
  return detail
    ? { title: detail.revision.title, spaceId: detail.article.spaceId }
    : null;
}

/** Управление доступом к пространству, коллекции или статье. */
export function AccessPage() {
  const { spaceId: spaceParam, collectionId, articleId } = useParams();
  const user = useCurrentUser();
  const article = useArticleTitle(articleId);
  const spaceId = spaceParam ?? article?.spaceId;
  const space = useSpace(spaceId);
  const navigation = useSpaceNavigation(collectionId ? spaceId : undefined);

  useEffect(() => {
    void loadSpaces();
  }, []);

  useEffect(() => {
    if (collectionId && spaceId) void loadNavigation(spaceId);
  }, [collectionId, spaceId]);

  const resource = useMemo<Resource | null>(() => {
    if (articleId) return { type: 'article', id: articleId };
    if (collectionId) return { type: 'collection', id: collectionId };
    if (spaceParam) return { type: 'space', id: spaceParam };
    return null;
  }, [articleId, collectionId, spaceParam]);

  const collectionTitle =
    collectionId && navigation?.data
      ? flattenCollections(navigation.data.collections).find(
          ({ node }) => node.id === collectionId,
        )?.node.title
      : undefined;

  const subject =
    resource?.type === 'article'
      ? article?.title
      : resource?.type === 'collection'
        ? collectionTitle
        : space?.name;

  const back =
    resource?.type === 'article'
      ? { to: routes.article(resource.id), label: 'Вернуться к статье' }
      : resource?.type === 'collection' && spaceId
        ? {
            to: `${routes.space(spaceId)}?collection=${resource.id}`,
            label: 'Вернуться к коллекции',
          }
        : {
            to: routes.space(spaceId ?? ''),
            label: 'Вернуться к пространству',
          };

  const crumbs: Crumb[] = [
    ...(space ? [{ label: space.name, to: routes.space(space.id) }] : []),
    ...(resource?.type === 'article' && article
      ? [{ label: article.title, to: routes.article(resource.id) }]
      : []),
    { label: 'Управление доступом' },
  ];

  if (!resource) return null;

  return (
    <>
      <AppHeader crumbs={crumbs} />
      <div className={styles.page}>
        <header className={styles.header}>
          <h1 className={styles.title}>{TITLES[resource.type]}</h1>
          {subject ? (
            <p className={styles.subtitle}>{subject}</p>
          ) : (
            <Skeleton height={18} width={280} />
          )}
        </header>

        {isAdmin(user) ? (
          <AccessManager
            resource={resource}
            space={space ? { id: space.id, name: space.name } : undefined}
          />
        ) : (
          <EmptyState
            title="Управлять доступом могут администраторы"
            description="Попросите администратора DIOS выдать или изменить права."
          />
        )}

        <footer className={styles.footer}>
          <ButtonLink to={back.to} className={styles.back}>
            {back.label}
          </ButtonLink>
          <p className={styles.hint}>
            Изменения доступа применяются на сервере.
          </p>
        </footer>
      </div>
    </>
  );
}
