import { Moon, Sun } from 'lucide-react';
import { toggleTheme, useTheme } from '@shared/lib/theme';
import { IconButton } from '@shared/ui/button';

export function ThemeToggle() {
  const dark = useTheme((state) => state.theme === 'dark');

  return (
    <IconButton
      icon={dark ? Moon : Sun}
      label={dark ? 'Светлая тема' : 'Тёмная тема'}
      onClick={toggleTheme}
    />
  );
}
