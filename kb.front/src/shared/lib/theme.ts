import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/** Сепия — тёплая светлая тема из настроек чтения */
export type Theme = 'light' | 'dark' | 'sepia';

interface ThemeState {
  theme: Theme;
}

const preferredTheme = (): Theme =>
  window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';

export const useTheme = create<ThemeState>()(
  persist(() => ({ theme: preferredTheme() }), { name: 'dios.theme' }),
);

export function setTheme(theme: Theme) {
  useTheme.setState({ theme });
}

/** Переключатель в шапке: тёмная ↔ светлая (сепия считается светлой). */
export function toggleTheme() {
  useTheme.setState(({ theme }) => ({
    theme: theme === 'dark' ? 'light' : 'dark',
  }));
}

/** Проставляет тему на <html> и следит за её сменой. */
export function syncThemeWithDocument() {
  const apply = ({ theme }: ThemeState) => {
    document.documentElement.dataset.theme = theme;
  };

  apply(useTheme.getState());
  return useTheme.subscribe(apply);
}
