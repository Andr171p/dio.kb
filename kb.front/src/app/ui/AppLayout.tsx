import clsx from 'clsx';
import { useState } from 'react';
import { Outlet, ScrollRestoration, useMatches } from 'react-router';
import { AppSidebar } from '@widgets/app-shell';
import { GlobalSearch } from '@widgets/global-search';
import { useHotkey } from '@shared/lib/hooks';
import { ConfirmHost } from '@shared/ui/dialog';
import { Toaster } from '@shared/ui/toast';
import styles from './AppLayout.module.scss';

/** Метаданные маршрута: `bare` — экран без навигации (режим фокуса). */
export interface RouteHandle {
  bare?: boolean;
}

export function AppLayout() {
  const [searchOpen, setSearchOpen] = useState(false);
  const bare = useMatches().some(
    (match) => (match.handle as RouteHandle | undefined)?.bare,
  );

  useHotkey('KeyK', () => setSearchOpen((open) => !open), {
    withModifier: true,
  });

  return (
    <div className={clsx(styles.layout, bare && styles.bare)}>
      {!bare && <AppSidebar />}
      <main className={styles.main}>
        <Outlet />
      </main>
      <GlobalSearch open={searchOpen} onClose={() => setSearchOpen(false)} />
      <ConfirmHost />
      <Toaster />
      <ScrollRestoration />
    </div>
  );
}
