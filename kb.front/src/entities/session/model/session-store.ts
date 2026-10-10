import { create } from 'zustand';
import {
  ApiError,
  authTokens,
  clearMediaCache,
  describeError,
  diosApi,
  type TokenPair,
} from '@shared/api';
import { resetStores } from '@shared/lib/store-reset';
import { clearUserStorage } from '@shared/lib/user-storage';
import type { User } from './types';

type SessionStatus = 'restoring' | 'authenticated' | 'anonymous';

interface SessionState {
  status: SessionStatus;
  user: User | null;
  /** Сессию не удалось восстановить из-за сети или сервера */
  restoreError: string | null;
}

export const useSession = create<SessionState>()(() => ({
  status: authTokens.hasSession() ? 'restoring' : 'anonymous',
  user: null,
  restoreError: null,
}));

async function loadUser() {
  const user = await diosApi.get<User>('/api/v1/users/me');
  useSession.setState({ status: 'authenticated', user, restoreError: null });
}

function endSession() {
  // Недоступное после выхода содержимое не должно остаться в кешах
  resetStores();
  clearUserStorage();
  clearMediaCache();
  useSession.setState({ status: 'anonymous', user: null, restoreError: null });
}

export async function restoreSession() {
  if (!authTokens.hasSession()) {
    endSession();
    return;
  }

  useSession.setState({ status: 'restoring', restoreError: null });
  try {
    await loadUser();
  } catch (error) {
    // 401 — сессия недействительна: подписка из initSession переведёт в anonymous
    if (error instanceof ApiError && error.status === 401) authTokens.clear();
    else useSession.setState({ restoreError: describeError(error) });
  }
}

export async function login(email: string, password: string) {
  const tokens = await diosApi.post<TokenPair>('/api/v1/auth/login', {
    form: { username: email, password },
    auth: false,
  });

  authTokens.save(tokens);
  await loadUser();
}

export async function logout() {
  try {
    // Гарантируем актуальную пару, чтобы отозвать именно действующий refresh-токен
    await authTokens.getAccessToken();
    await diosApi.post('/api/v1/auth/logout', {
      body: { refresh_token: authTokens.getRefreshToken() },
    });
  } catch {
    // Сервер недоступен — всё равно завершаем сессию локально
  }
  authTokens.clear();
}

/** Восстанавливает сессию и синхронизирует вход/выход между вкладками. */
export function initSession() {
  authTokens.subscribe((active) => {
    if (active) void restoreSession();
    else endSession();
  });

  void restoreSession();
}

export function useCurrentUser(): User | null {
  return useSession((state) => state.user);
}
