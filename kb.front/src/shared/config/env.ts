const list = (value: string | undefined) =>
  (value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

export const env = {
  /** Сервис авторизации DIOS (IAM, Media Service) */
  authApiUrl: import.meta.env.VITE_AUTH_API_URL ?? '/auth-api',
  /** Сервис базы знаний */
  kbApiUrl: import.meta.env.VITE_KB_API_URL ?? '/kb-api',
  /** Фронт DIOS: ссылки на заявки и возврат в DIOS */
  diosUrl: import.meta.env.VITE_DIOS_URL ?? 'http://localhost:3001',
  /** Справка по базе знаний: ссылка «Помощь» в шапке, скрыта, если не задана */
  helpUrl: import.meta.env.VITE_HELP_URL ?? '',
  /** Сервисы экосистемы DIOS: ссылки на них открываются без предупреждения */
  trustedOrigins: list(import.meta.env.VITE_TRUSTED_ORIGINS),
} as const;
