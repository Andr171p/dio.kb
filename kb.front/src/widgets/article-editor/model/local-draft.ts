import { USER_STORAGE_PREFIX } from '@shared/lib/user-storage';

/**
 * Страховочная копия несохранённого текста в браузере: переживает закрытие вкладки.
 * Редакции на сервере создаются только явным сохранением — автосохранение засорило бы историю.
 */
export interface LocalDraft {
  title: string;
  summary: string;
  content: string;
  /** Редакция, от которой начали правки; null — новая статья */
  baseRevisionId: string | null;
  savedAt: string;
}

const PREFIX = `${USER_STORAGE_PREFIX}draft.`;

const storageKey = (userId: string, target: string) =>
  `${PREFIX}${userId}.${target}`;

export function readLocalDraft(
  userId: string,
  target: string,
): LocalDraft | null {
  try {
    const raw = localStorage.getItem(storageKey(userId, target));
    return raw ? (JSON.parse(raw) as LocalDraft) : null;
  } catch {
    return null;
  }
}

export function writeLocalDraft(
  userId: string,
  target: string,
  draft: Omit<LocalDraft, 'savedAt'>,
) {
  try {
    localStorage.setItem(
      storageKey(userId, target),
      JSON.stringify({ ...draft, savedAt: new Date().toISOString() }),
    );
  } catch {
    // Хранилище переполнено или недоступно — работаем без страховки
  }
}

export function clearLocalDraft(userId: string, target: string) {
  try {
    localStorage.removeItem(storageKey(userId, target));
  } catch {
    // Хранилище недоступно
  }
}
