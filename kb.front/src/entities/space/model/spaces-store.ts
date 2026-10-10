import { create } from 'zustand';
import { describeError, kbApi } from '@shared/api';
import { registerStoreReset } from '@shared/lib/store-reset';
import type { Space } from './types';

interface SpacesState {
  status: 'idle' | 'loading' | 'ready' | 'error';
  items: Space[];
  error: string | null;
}

export const useSpaces = create<SpacesState>()(() => ({
  status: 'idle',
  items: [],
  error: null,
}));

registerStoreReset(() => useSpaces.setState(useSpaces.getInitialState(), true));

let pending: Promise<void> | null = null;

/** Пространства, доступные пользователю на чтение. Повторные вызовы во время загрузки объединяются. */
export function loadSpaces(): Promise<void> {
  pending ??= (async () => {
    if (useSpaces.getState().status !== 'ready')
      useSpaces.setState({ status: 'loading', error: null });
    try {
      const items = await kbApi.get<Space[]>('/api/user/v1/spaces');
      useSpaces.setState({ status: 'ready', items, error: null });
    } catch (error) {
      useSpaces.setState({ status: 'error', error: describeError(error) });
    } finally {
      pending = null;
    }
  })();
  return pending;
}

export function upsertSpace(space: Space) {
  useSpaces.setState(({ items }) => {
    const rest = items.filter((item) => item.id !== space.id);
    return {
      items: [...rest, space].sort((a, b) =>
        a.name.localeCompare(b.name, 'ru'),
      ),
    };
  });
}

export function removeSpace(spaceId: string) {
  useSpaces.setState(({ items }) => ({
    items: items.filter((item) => item.id !== spaceId),
  }));
}

export function useSpace(spaceId: string | undefined): Space | undefined {
  return useSpaces((state) =>
    state.items.find((space) => space.id === spaceId),
  );
}
