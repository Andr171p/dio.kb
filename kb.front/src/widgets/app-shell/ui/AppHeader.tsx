import { ArrowLeft, Menu as MenuIcon } from 'lucide-react';
import type { ReactNode } from 'react';
import { Link } from 'react-router';
import { ThemeToggle } from '@features/toggle-theme';
import { env } from '@shared/config/env';
import { routes } from '@shared/config/routes';
import { useMediaQuery } from '@shared/lib/hooks';
import { Breadcrumbs, type Crumb } from '@shared/ui/breadcrumbs';
import { IconButton } from '@shared/ui/button';
import { Logo } from '@shared/ui/logo';
import { Topbar } from '@shared/ui/topbar';
import { setMobileSidebarOpen } from '../model/sidebar-store';
import styles from './AppHeader.module.scss';

interface AppHeaderProps {
  /** Путь до текущего экрана: последний элемент — сам экран */
  crumbs: Crumb[];
  /** Действия экрана справа: на мобильных — рядом с кнопкой навигации */
  actions?: ReactNode;
}

/**
 * Шапка экрана: путь слева, тема и помощь справа. На мобильных — возврат
 * на уровень выше (или логотип) и кнопка навигации.
 */
export function AppHeader({ crumbs, actions }: AppHeaderProps) {
  const mobile = useMediaQuery('(max-width: 900px)');
  const parent = crumbs
    .slice(0, -1)
    .reverse()
    .find((crumb) => crumb.to);

  if (mobile)
    return (
      <Topbar
        start={
          parent?.to ? (
            <Link to={parent.to} className={styles.back}>
              <ArrowLeft size={16} aria-hidden />
              {/* С действиями экрана на виду остаётся только стрелка */}
              <span
                className={actions ? styles.visuallyHidden : styles.backLabel}
              >
                {parent.label}
              </span>
            </Link>
          ) : (
            <Link to={routes.home()} className={styles.logo}>
              <Logo size={30} />
            </Link>
          )
        }
        end={
          <>
            {actions}
            <IconButton
              icon={MenuIcon}
              label="Навигация"
              tooltip={false}
              size="md"
              onClick={() => setMobileSidebarOpen(true)}
            />
          </>
        }
      />
    );

  return (
    <Topbar
      start={<Breadcrumbs items={crumbs} />}
      end={
        <>
          {actions}
          <ThemeToggle />
          {env.helpUrl && (
            <a
              href={env.helpUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.help}
            >
              Помощь
            </a>
          )}
        </>
      }
    />
  );
}
