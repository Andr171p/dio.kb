import { useEffect } from 'react';
import { create } from 'zustand';
import { diosApi } from '@shared/api';
import { registerStoreReset } from '@shared/lib/store-reset';

/** Публичные данные пользователя DIOS для подписи авторов и выдачи доступа. */
export interface UserProfile {
  id: string;
  email: string;
  username: string | null;
  full_name: string | null;
  avatar_url: string | null;
}

interface UsersState {
  /** null — пользователь не найден или недоступен */
  byId: Record<string, UserProfile | null | undefined>;
}

export const useUsers = create<UsersState>()(() => ({ byId: {} }));

registerStoreReset(() => useUsers.setState(useUsers.getInitialState(), true));

const requested = new Set<string>();

async function loadUser(userId: string) {
  try {
    const user = await diosApi.get<UserProfile>(`/api/v1/users/${userId}`);
    useUsers.setState(({ byId }) => ({ byId: { ...byId, [userId]: user } }));
  } catch {
    useUsers.setState(({ byId }) => ({ byId: { ...byId, [userId]: null } }));
  }
}

export function ensureUsers(userIds: Iterable<string>) {
  for (const id of userIds) {
    if (requested.has(id)) continue;
    requested.add(id);
    void loadUser(id);
  }
}

registerStoreReset(() => requested.clear());

export function userDisplayName(user: UserProfile): string {
  return user.full_name ?? user.username ?? user.email;
}

/** Имя пользователя по id; пока профиль грузится — undefined. */
export function useUserName(
  userId: string | null | undefined,
): string | undefined {
  const user = useUsers((state) => (userId ? state.byId[userId] : undefined));

  useEffect(() => {
    if (userId) ensureUsers([userId]);
  }, [userId]);

  if (user === null) return 'Неизвестный пользователь';
  return user ? userDisplayName(user) : undefined;
}
