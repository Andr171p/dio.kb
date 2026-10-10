import type { Permission } from '@entities/access-grant';
import type { ArticleStatus } from '@entities/article';

export type TargetType = 'collection' | 'article';

/** Контейнер навигации. Размещение статьи в коллекции не даёт прав на её содержимое. */
export interface Collection {
  id: string;
  createdAt: string;
  updatedAt: string;
  spaceId: string;
  name: string;
  slug: string;
  description: string | null;
  permissions: Permission[];
}

export interface CollectionTarget {
  type: TargetType;
  id: string;
}

/** Размещение коллекции или статьи в коллекции с порядком `rank`. */
export interface CollectionPlacement {
  id: string;
  collectionId: string;
  target: CollectionTarget;
  rank: string;
}

export interface NavigationNode {
  type: TargetType;
  id: string;
  /** Размещение узла; у корневых коллекций его нет */
  placementId: string | null;
  title: string;
  slug: string;
  status: ArticleStatus | null;
  children: NavigationNode[];
}

export interface SpaceNavigation {
  collections: NavigationNode[];
  unplacedArticles: NavigationNode[];
}

export interface RelativePosition {
  beforeId?: string;
  afterId?: string;
}
