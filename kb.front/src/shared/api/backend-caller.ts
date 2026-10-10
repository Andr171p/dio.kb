import { ApiError, toApiError } from './api-error';
import { authTokens } from './auth-tokens';

type QueryValue = string | number | boolean | null | undefined;

export interface RequestOptions {
  query?: Record<string, QueryValue>;
  /** JSON-тело запроса */
  body?: unknown;
  /** Тело в формате application/x-www-form-urlencoded */
  form?: Record<string, string>;
  signal?: AbortSignal;
  /** Подставлять ли access-токен. По умолчанию — да */
  auth?: boolean;
}

/**
 * Тонкая обёртка над fetch: базовый URL, авторизация, повтор после 401 и единый формат ошибок.
 */
export class BackendCaller {
  readonly #baseUrl: string;

  constructor(baseUrl: string) {
    this.#baseUrl = baseUrl;
  }

  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.#json<T>('GET', path, options);
  }

  post<T = void>(path: string, options?: RequestOptions): Promise<T> {
    return this.#json<T>('POST', path, options);
  }

  patch<T = void>(path: string, options?: RequestOptions): Promise<T> {
    return this.#json<T>('PATCH', path, options);
  }

  delete(path: string, options?: RequestOptions): Promise<void> {
    return this.#json<void>('DELETE', path, options);
  }

  async #json<T>(
    method: string,
    path: string,
    options?: RequestOptions,
  ): Promise<T> {
    const response = await this.#send(method, path, options);
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  async #send(
    method: string,
    path: string,
    { query, body, form, signal, auth = true }: RequestOptions = {},
  ): Promise<Response> {
    const request = (token: string | null) =>
      fetch(this.#url(path, query), {
        method,
        signal,
        headers: {
          ...(body !== undefined && { 'Content-Type': 'application/json' }),
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: form
          ? new URLSearchParams(form)
          : body !== undefined
            ? JSON.stringify(body)
            : undefined,
      });

    let token = auth ? await authTokens.getAccessToken() : null;
    if (auth && !token) throw new ApiError(401, 'Требуется авторизация');

    let response = await request(token);

    if (token && response.status === 401) {
      token = await authTokens.renewAccessToken(token);
      if (!token) throw new ApiError(401, 'Сессия истекла, войдите снова');
      response = await request(token);
    }

    if (!response.ok) throw await toApiError(response);
    return response;
  }

  #url(path: string, query: Record<string, QueryValue> = {}): string {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== null && value !== undefined) params.set(key, String(value));
    }

    const search = params.size > 0 ? `?${params.toString()}` : '';
    return `${this.#baseUrl}${path}${search}`;
  }
}
