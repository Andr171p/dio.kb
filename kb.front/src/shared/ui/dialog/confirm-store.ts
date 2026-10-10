import { create } from 'zustand';

export interface ConfirmOptions {
  title: string;
  description?: string;
  confirmLabel: string;
  tone?: 'primary' | 'danger';
  /** Выполняется по подтверждению; диалог закрывается после успеха */
  onConfirm: () => Promise<unknown> | void;
}

interface ConfirmState {
  options: ConfirmOptions | null;
}

export const useConfirm = create<ConfirmState>()(() => ({ options: null }));

/** Подтверждение необратимого или заметного действия: архивирование, снятие с публикации. */
export function confirmAction(options: ConfirmOptions) {
  useConfirm.setState({ options });
}
