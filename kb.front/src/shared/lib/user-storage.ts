/**
 * Префикс данных пользователя в localStorage (черновики, недавние статьи).
 * Всё под ним удаляется при выходе из аккаунта.
 */
export const USER_STORAGE_PREFIX = 'dios.kb.user.';

export function clearUserStorage() {
  try {
    Object.keys(localStorage)
      .filter((key) => key.startsWith(USER_STORAGE_PREFIX))
      .forEach((key) => localStorage.removeItem(key));
  } catch {
    // Хранилище недоступно
  }
}
