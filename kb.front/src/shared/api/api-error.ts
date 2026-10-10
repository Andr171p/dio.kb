export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

interface ErrorBody {
  /** Формат DIO desk */
  error?: { code?: string; message?: string; public_message?: string };
  /** Формат Knowledge API */
  errorCode?: string;
  /** Формат валидации FastAPI */
  detail?: string | { msg?: string }[];
}

const STATUS_MESSAGES: Record<number, string> = {
  401: 'Требуется авторизация',
  403: 'Недостаточно прав для этого действия',
  404: 'Не найдено',
  409: 'Данные изменились, обновите страницу',
  422: 'Проверьте введённые данные',
  429: 'Слишком много запросов, попробуйте позже',
};

export async function toApiError(response: Response): Promise<ApiError> {
  const body = (await response.json().catch(() => null)) as ErrorBody | null;
  const detail = Array.isArray(body?.detail)
    ? body.detail[0]?.msg
    : body?.detail;
  const message =
    body?.error?.public_message ??
    STATUS_MESSAGES[response.status] ??
    (response.status >= 500 ? 'Сервис временно недоступен' : undefined) ??
    detail ??
    'Не удалось выполнить запрос';

  return new ApiError(
    response.status,
    message,
    body?.error?.code ?? body?.errorCode,
  );
}

/** Текст ошибки, который можно показать пользователю. */
export function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof TypeError) return 'Нет соединения с сервером';
  return 'Что-то пошло не так';
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}
