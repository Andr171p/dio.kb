import { env } from '../config/env';
import { toApiError } from './api-error';

/** Пара токенов сервиса авторизации DIO desk. */
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  /** Unix-время истечения access-токена в секундах */
  expires_at: number;
}

type SessionListener = (active: boolean) => void;

const REFRESH_TOKEN_KEY = 'dios.auth.refresh-token';
const REFRESH_LOCK = 'dios.auth.refresh';
/** Обновляем access заранее, чтобы он не истёк по дороге до сервера */
const EXPIRY_MARGIN_MS = 30_000;

/**
 * Access-токен живёт только в памяти вкладки и никогда не попадает в хранилище.
 * Refresh-токен хранится в localStorage и ротируется при каждом обновлении.
 */
let access: { token: string; expiresAt: number } | null = null;
let pendingRefresh: Promise<string | null> | null = null;
const listeners = new Set<SessionListener>();

function readRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

function writeRefreshToken(token: string | null) {
  try {
    if (token) localStorage.setItem(REFRESH_TOKEN_KEY, token);
    else localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch {
    // Хранилище недоступно (приватный режим) — сессия проживёт до перезагрузки
  }
}

function currentAccessToken(): string | null {
  return access && access.expiresAt - EXPIRY_MARGIN_MS > Date.now()
    ? access.token
    : null;
}

function save(tokens: TokenPair) {
  access = { token: tokens.access_token, expiresAt: tokens.expires_at * 1000 };
  writeRefreshToken(tokens.refresh_token);
}

function clear() {
  access = null;
  writeRefreshToken(null);
  listeners.forEach((listener) => listener(false));
}

async function requestNewTokens(): Promise<string | null> {
  // Читаем уже под блокировкой: соседняя вкладка могла успеть ротировать токен
  const refreshToken = readRefreshToken();
  if (!refreshToken) {
    clear();
    return null;
  }

  const response = await fetch(`${env.authApiUrl}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if ([401, 403, 422].includes(response.status)) {
    clear();
    return null;
  }
  // Сетевые и серверные сбои не должны разлогинивать пользователя
  if (!response.ok) throw await toApiError(response);

  const tokens = (await response.json()) as TokenPair;
  save(tokens);
  return tokens.access_token;
}

function refresh(): Promise<string | null> {
  // Web Locks сериализуют ротацию между вкладками: один refresh-токен не уйдёт на сервер дважды
  const run = () =>
    'locks' in navigator
      ? navigator.locks.request(REFRESH_LOCK, requestNewTokens)
      : requestNewTokens();

  pendingRefresh ??= run().finally(() => {
    pendingRefresh = null;
  });
  return pendingRefresh;
}

function onStorage(event: StorageEvent) {
  if (event.key !== REFRESH_TOKEN_KEY && event.key !== null) return;

  if (event.newValue === null) {
    // Выход в соседней вкладке
    access = null;
    listeners.forEach((listener) => listener(false));
  } else if (event.oldValue === null) {
    // Вход в соседней вкладке
    listeners.forEach((listener) => listener(true));
  }
}

export const authTokens = {
  hasSession: () => readRefreshToken() !== null,

  getRefreshToken: readRefreshToken,

  save,

  /** Удаляет токены и оповещает подписчиков о завершении сессии. */
  clear,

  /** Актуальный access-токен; при необходимости обновляет пару токенов. */
  getAccessToken(): Promise<string | null> {
    const token = currentAccessToken();
    return token ? Promise.resolve(token) : refresh();
  },

  /** Сервер отклонил `rejected` — получаем новый, если его ещё не получил параллельный запрос. */
  renewAccessToken(rejected: string): Promise<string | null> {
    const token = currentAccessToken();
    return token && token !== rejected ? Promise.resolve(token) : refresh();
  },

  /** Подписка на начало и завершение сессии, в том числе в соседних вкладках. */
  subscribe(listener: SessionListener): () => void {
    if (listeners.size === 0) window.addEventListener('storage', onStorage);
    listeners.add(listener);

    return () => {
      listeners.delete(listener);
      if (listeners.size === 0)
        window.removeEventListener('storage', onStorage);
    };
  },
};
