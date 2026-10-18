import { createContext } from 'react';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { registerStoreReset } from '@shared/lib/store-reset';
import { USER_STORAGE_PREFIX } from '@shared/lib/user-storage';

const LIMIT = 500;

interface ChecklistState {
  /** `${revisionId}:${позиция пункта в Markdown}` → отмечен ли пункт */
  marks: Record<string, boolean>;
}

/**
 * Отметки чеклистов при чтении — личные заметки в этом браузере.
 * Текст статьи не меняется; ключ привязан к редакции, поэтому после
 * новой публикации отметки начинаются заново.
 */
export const useChecklists = create<ChecklistState>()(
  persist((): ChecklistState => ({ marks: {} }), {
    name: `${USER_STORAGE_PREFIX}checklists`,
  }),
);

registerStoreReset(() => useChecklists.setState({ marks: {} }));

export function toggleChecklistItem(id: string, checked: boolean) {
  useChecklists.setState(({ marks }) => {
    const next = { ...marks, [id]: checked };
    const keys = Object.keys(next);
    // Храним только последние отметки, чтобы localStorage не рос бесконечно
    if (keys.length > LIMIT)
      keys.slice(0, keys.length - LIMIT).forEach((key) => delete next[key]);
    return { marks: next };
  });
}

/** Ключ редакции: если задан, чекбоксы в тексте можно отмечать. */
export const ChecklistContext = createContext<string | null>(null);
