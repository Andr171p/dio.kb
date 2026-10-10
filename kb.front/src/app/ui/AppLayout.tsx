import clsx from 'clsx';
import { useState } from 'react';
import { Outlet, ScrollRestoration } from 'react-router';
import { AppSidebar, useSidebar } from '@widgets/app-sidebar';
import { GlobalSearch } from '@widgets/global-search';
import { useHotkey } from '@shared/lib/hooks';
import { ConfirmHost } from '@shared/ui/dialog';
import { Toaster } from '@shared/ui/toast';
import styles from './AppLayout.module.scss';

export function AppLayout() {
  const collapsed = useSidebar((state) => state.collapsed);
  const [searchOpen, setSearchOpen] = useState(false);

  useHotkey('KeyK', () => setSearchOpen((open) => !open), {
    withModifier: true,
  });

  return (
    <div className={clsx(styles.layout, collapsed && styles.collapsed)}>
      <div className={styles.backdrop} aria-hidden />
      <AppSidebar onOpenSearch={() => setSearchOpen(true)} />
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
