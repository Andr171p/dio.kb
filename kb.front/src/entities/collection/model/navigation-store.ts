import { create } from 'zustand';
import { describeError, kbApi } from '@shared/api';
import { registerStoreReset } from '@shared/lib/store-reset';
import type { NavigationNode, SpaceNavigation } from './types';

interface NavigationEntry {
  status: 'loading' | 'ready' | 'error';
  data: SpaceNavigation | null;
  error: string | null;
}

interface NavigationState {
  bySpace: Record<string, NavigationEntry | undefined>;
}

export const useNavigationTree = create<NavigationState>()(() => ({
  bySpace: {},
}));

registerStoreReset(() =>
  useNavigationTree.setState(useNavigationTree.getInitialState(), true),
);

const pending = new Map<string, Promise<void>>();

function patch(spaceId: string, entry: Partial<NavigationEntry>) {
  useNavigationTree.setState(({ bySpace }) => ({
    bySpace: {
      ...bySpace,
      [spaceId]: {
        status: 'loading',
        data: null,
        error: null,
        ...bySpace[spaceId],
        ...entry,
      },
    },
  }));
}

/** Дерево навигации пространства. Без `force` уже загруженное дерево не перезапрашивается. */
export function loadNavigation(
  spaceId: string,
  { force = false } = {},
): Promise<void> {
  const current = useNavigationTree.getState().bySpace[spaceId];
  if (!force && current?.status === 'ready') return Promise.resolve();

  const existing = pending.get(spaceId);
  if (existing) return existing;

  // Повторная загрузка не прячет уже показанное дерево
  if (!current?.data) patch(spaceId, { status: 'loading', error: null });

  const request = kbApi
    .get<SpaceNavigation>(`/api/user/v1/spaces/${spaceId}/navigation`)
    .then((data) => patch(spaceId, { status: 'ready', data, error: null }))
    .catch((error: unknown) =>
      patch(spaceId, { status: 'error', error: describeError(error) }),
    )
    .finally(() => pending.delete(spaceId));

  pending.set(spaceId, request);
  return request;
}

/** Перечитать дерево после изменения структуры (создание, перемещение, архивирование). */
export function refreshNavigation(spaceId: string): Promise<void> {
  return loadNavigation(spaceId, { force: true });
}

export function useSpaceNavigation(
  spaceId: string | undefined,
): NavigationEntry | undefined {
  return useNavigationTree((state) =>
    spaceId ? state.bySpace[spaceId] : undefined,
  );
}

/** Все коллекции дерева плоским списком с глубиной — для выбора родителя. */
export function flattenCollections(
  nodes: NavigationNode[],
  depth = 0,
): { node: NavigationNode; depth: number }[] {
  return nodes
    .filter((node) => node.type === 'collection')
    .flatMap((node) => [
      { node, depth },
      ...flattenCollections(node.children, depth + 1),
    ]);
}

/** Путь от корня до узла (включительно) — для хлебных крошек и раскрытия дерева. */
export function findNodePath(
  navigation: SpaceNavigation,
  predicate: (node: NavigationNode) => boolean,
): NavigationNode[] | null {
  const walk = (nodes: NavigationNode[]): NavigationNode[] | null => {
    for (const node of nodes) {
      if (predicate(node)) return [node];
      const path = walk(node.children);
      if (path) return [node, ...path];
    }
    return null;
  };
  return walk(navigation.collections) ?? walk(navigation.unplacedArticles);
}
