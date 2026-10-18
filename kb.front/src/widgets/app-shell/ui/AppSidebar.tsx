import clsx from 'clsx';
import {
  ArrowUpRight,
  Clock,
  House,
  LogOut,
  Plus,
  Search,
  X,
  type LucideIcon,
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
import { Avatar } from '@shared/ui/avatar';
import { IconButton } from '@shared/ui/button';
import { Logo } from '@shared/ui/logo';
import { Menu, MenuItem, MenuSeparator } from '@shared/ui/menu';
import { usePopover } from '@shared/ui/popover';
import { Skeleton } from '@shared/ui/skeleton';
import {
  openSidebarDialog,
  setMobileSidebarOpen,
  useSidebar,
} from '../model/sidebar-store';
import { SpaceTree } from './NavigationTree';
import { SidebarDialogs } from './SidebarDialogs';
import styles from './AppSidebar.module.scss';

function NavItem({
  to,
  icon: Icon,
  end,
  children,
}: {
  to: string;
  icon: LucideIcon;
  end?: boolean;
  children: string;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        clsx(styles.navItem, isActive && styles.navActive)
      }
    >
      <Icon size={17} strokeWidth={1.7} aria-hidden />
      {children}
    </NavLink>
  );
}

function UserMenu() {
  const user = useCurrentUser();
  const { triggerProps, popoverProps } = usePopover();
  if (!user) return null;

  const name = displayName(user);

  return (
    <>
      <button type="button" className={styles.user} {...triggerProps}>
        <Avatar name={name} size={30} />
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

/** Навигация по базе знаний: разделы, пространства с деревом коллекций и профиль. */
export function AppSidebar() {
  const user = useCurrentUser();
  const { status, items: spaces, error } = useSpaces();
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
        className={clsx(styles.sidebar, mobileOpen && styles.mobileOpen)}
        aria-label="Навигация"
      >
        <div className={styles.header}>
          <NavLink to={routes.home()} className={styles.logo}>
            <Logo />
          </NavLink>
          <IconButton
            icon={X}
            label="Закрыть навигацию"
            className={styles.close}
            onClick={() => setMobileSidebarOpen(false)}
          />
        </div>

        <nav className={styles.nav} aria-label="Разделы">
          <NavItem to={routes.home()} icon={House} end>
            Главная
          </NavItem>
          <NavItem to={routes.search()} icon={Search}>
            Поиск
          </NavItem>
          <NavItem to={routes.recent()} icon={Clock}>
            Недавние
          </NavItem>
        </nav>

        <div className={styles.sectionHeader}>
          <span className={styles.sectionLabel}>Пространства</span>
          {isAdmin(user) && (
            <IconButton
              icon={Plus}
              label="Новое пространство"
              className={styles.sectionAction}
              onClick={() => openSidebarDialog({ kind: 'create-space' })}
            />
          )}
        </div>

        <ul role="tree" aria-label="Пространства" className={styles.tree}>
          {status === 'loading' && spaces.length === 0 && (
            <li className={styles.treeSkeleton}>
              <Skeleton height={16} width="80%" />
              <Skeleton height={16} width="60%" />
              <Skeleton height={16} width="70%" />
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
          {/* На мобильных шапка не показывает тему — переключатель здесь */}
          <span className={styles.mobileTheme}>
            <ThemeToggle />
          </span>
        </div>
      </aside>
      <SidebarDialogs />
    </>
  );
}
