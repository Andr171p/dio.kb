import { create } from 'zustand';

type ToastTone = 'success' | 'error' | 'info';

export interface ToastItem {
  id: number;
  tone: ToastTone;
  message: string;
}

interface ToastState {
  items: ToastItem[];
}

export const useToasts = create<ToastState>()(() => ({ items: [] }));

const DURATION_MS: Record<ToastTone, number> = {
  success: 3500,
  info: 4500,
  error: 7000,
};

let nextId = 1;

function show(tone: ToastTone, message: string) {
  const id = nextId++;
  useToasts.setState(({ items }) => ({
    items: [...items.slice(-3), { id, tone, message }],
  }));
  setTimeout(() => dismissToast(id), DURATION_MS[tone]);
}

export function dismissToast(id: number) {
  useToasts.setState(({ items }) => ({
    items: items.filter((item) => item.id !== id),
  }));
}

/** Короткое сообщение о результате операции (сохранение, публикация, ошибка). */
export const toast = {
  success: (message: string) => show('success', message),
  error: (message: string) => show('error', message),
  info: (message: string) => show('info', message),
};
