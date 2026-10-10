import clsx from 'clsx';
import {
  ArrowUpRight,
  Home,
  LogOut,
  PanelLeftClose,
  Plus,
  Search,
  TextSearch,
} from 'lucide-react';
import { useEffect } from 'react';
import { NavLink, useLocation } from 'react-router';
import {
  displayName,
  isAdmin,
  logout,
  useCurrentUser,
} from '@entities/session';
import { loadSpaces, useSpaces } from '@entities/space';
import { ThemeToggle } from '@features/toggle-theme';
import { env } from '@shared/config/env';
import { routes } from '@shared/config/routes';
import { MOD_KEY_LABEL } from '@shared/lib/hooks';
import { Avatar } from '@shared/ui/avatar';
import { IconButton } from '@shared/ui/button';
import { Kbd } from '@shared/ui/kbd';
import { Logo } from '@shared/ui/logo';
import { Menu, MenuItem, MenuSeparator } from '@shared/ui/menu';
import { usePopover } from '@shared/ui/popover';
import { Skeleton } from '@shared/ui/skeleton';
import {
  openSidebarDialog,
  setMobileSidebarOpen,
  toggleSidebar,
  useSidebar,
} from '../model/sidebar-store';
import { SpaceTree } from './NavigationTree';
import { SidebarDialogs } from './SidebarDialogs';
import styles from './AppSidebar.module.scss';

interface AppSidebarProps {
  onOpenSearch: () => void;
}

function UserMenu() {
  const user = useCurrentUser();
  const { triggerProps, popoverProps } = usePopover();
  if (!user) return null;

  const name = displayName(user);

  return (
    <>
      <button type="button" className={styles.user} {...triggerProps}>
        <Avatar name={name} size={28} />
        <span className={styles.userText}>
          <span className={styles.userName}>{name}</span>
          <span className={styles.userEmail}>{user.email}</span>
        </span>
      </button>
      <Menu {...popoverProps} placement="top-start">
        <MenuItem
          icon={ArrowUpRight}
          onSelect={() => window.open(env.diosUrl, '_blank', 'noopener')}
        >
          Открыть DIOS
        </MenuItem>
        <MenuSeparator />
        <MenuItem icon={LogOut} onSelect={() => void logout()}>
          Выйти
        </MenuItem>
      </Menu>
    </>
  );
}

/** Навигация по базе знаний. Стеклянная панель поверх фона приложения. */
export function AppSidebar({ onOpenSearch }: AppSidebarProps) {
  const user = useCurrentUser();
  const { status, items: spaces, error } = useSpaces();
  const collapsed = useSidebar((state) => state.collapsed);
  const mobileOpen = useSidebar((state) => state.mobileOpen);
  const location = useLocation();

  useEffect(() => {
    void loadSpaces();
  }, []);

  // На мобильных панель закрывается после перехода
  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [location.pathname]);

  return (
    <>
      <div
        className={clsx(styles.scrim, mobileOpen && styles.scrimVisible)}
        onClick={() => setMobileSidebarOpen(false)}
        aria-hidden
      />
      <aside
        className={clsx(
          styles.sidebar,
          collapsed && styles.collapsed,
          mobileOpen && styles.mobileOpen,
        )}
        aria-label="Навигация"
      >
        <div className={styles.header}>
          <NavLink to={routes.home()} className={styles.logo}>
            <Logo />
          </NavLink>
          <IconButton
            icon={PanelLeftClose}
            label="Скрыть панель"
            className={styles.collapseButton}
            onClick={() => {
              if (mobileOpen) setMobileSidebarOpen(false);
              else toggleSidebar();
            }}
          />
        </div>

        <button
          type="button"
          className={styles.searchTrigger}
          onClick={onOpenSearch}
        >
          <Search size={15} aria-hidden />
          <span className={styles.searchLabel}>Поиск…</span>
          <Kbd keys={[MOD_KEY_LABEL, 'K']} />
        </button>

        <nav className={styles.nav}>
          <NavLink
            to={routes.home()}
            end
            className={({ isActive }) =>
              clsx(styles.navItem, isActive && styles.navActive)
            }
          >
            <Home size={16} aria-hidden />
            Главная
          </NavLink>
          <NavLink
            to={routes.search()}
            className={({ isActive }) =>
              clsx(styles.navItem, isActive && styles.navActive)
            }
          >
            <TextSearch size={16} aria-hidden />
            Поиск по содержимому
          </NavLink>
        </nav>

        <div className={styles.sectionHeader}>
          <span className={styles.sectionLabel}>Пространства</span>
          {isAdmin(user) && (
            <IconButton
              icon={Plus}
              label="Новое пространство"
              onClick={() => openSidebarDialog({ kind: 'create-space' })}
            />
          )}
        </div>

        <ul role="tree" aria-label="Пространства" className={styles.tree}>
          {status === 'loading' && spaces.length === 0 && (
            <li className={styles.treeSkeleton}>
              <Skeleton height={14} width="80%" />
              <Skeleton height={14} width="60%" />
              <Skeleton height={14} width="70%" />
            </li>
          )}
          {status === 'error' && (
            <li className={styles.treeMessage}>
              {error}{' '}
              <button
                type="button"
                className={styles.retry}
                onClick={() => void loadSpaces()}
              >
                Повторить
              </button>
            </li>
          )}
          {status === 'ready' && spaces.length === 0 && (
            <li className={styles.treeMessage}>
              Нет доступных пространств. Попросите администратора выдать доступ.
            </li>
          )}
          {spaces.map((space) => (
            <SpaceTree key={space.id} space={space} />
          ))}
        </ul>

        <div className={styles.footer}>
          <UserMenu />
          <ThemeToggle />
        </div>
      </aside>
      <SidebarDialogs />
    </>
  );
}
