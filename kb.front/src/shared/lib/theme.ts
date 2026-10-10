import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Theme = 'light' | 'dark';

interface ThemeState {
  theme: Theme;
}

const preferredTheme = (): Theme =>
  window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';

export const useTheme = create<ThemeState>()(
  persist(() => ({ theme: preferredTheme() }), { name: 'dios.theme' }),
);

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
