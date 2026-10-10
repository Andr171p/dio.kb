import {
  refreshNavigation,
  type Collection,
  type CollectionPlacement,
  type CollectionTarget,
  type RelativePosition,
} from '@entities/collection';
import { describeError, kbApi } from '@shared/api';
import { toast } from '@shared/ui/toast';

/** Ошибку показываем тостом и пробрасываем дальше: диалог подтверждения останется открытым. */
async function run<T>(spaceId: string, action: () => Promise<T>): Promise<T> {
  try {
    return await action();
  } catch (error) {
    toast.error(describeError(error));
    throw error;
  } finally {
    // Сервер — источник истины о структуре: перечитываем дерево и после ошибки
    void refreshNavigation(spaceId);
  }
}

export function renameCollection(
  spaceId: string,
  collectionId: string,
  changes: { name: string; description?: string },
) {
  return run(spaceId, () =>
    kbApi.patch<Collection>(`/api/user/v1/collections/${collectionId}`, {
      body: changes,
    }),
  );
}

/** Архивировать можно только пустую коллекцию — иначе backend вернёт 409. */
export function archiveCollection(spaceId: string, collectionId: string) {
  return run(spaceId, () =>
    kbApi.delete(`/api/user/v1/collections/${collectionId}`),
  );
}

export function addToCollection(
  spaceId: string,
  collectionId: string,
  target: CollectionTarget,
  position: RelativePosition = {},
) {
  return run(spaceId, () =>
    kbApi.post<CollectionPlacement>(
      `/api/user/v1/collections/${collectionId}/placements`,
      { body: { target, position } },
    ),
  );
}

export function movePlacement(
  spaceId: string,
  placementId: string,
  move: { collectionId?: string; position?: RelativePosition },
) {
  return run(spaceId, () =>
    kbApi.patch<CollectionPlacement>(`/api/user/v1/placements/${placementId}`, {
      body: move,
    }),
  );
}

export function removePlacement(spaceId: string, placementId: string) {
  return run(spaceId, () =>
    kbApi.delete(`/api/user/v1/placements/${placementId}`),
  );
}
