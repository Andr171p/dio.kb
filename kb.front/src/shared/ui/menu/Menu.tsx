import clsx from 'clsx';
import type { LucideIcon } from 'lucide-react';
import { createContext, use, type ComponentProps, type ReactNode } from 'react';
import { Popover } from '../popover';
import styles from './Menu.module.scss';

const MenuContext = createContext<string | null>(null);

type MenuProps = ComponentProps<typeof Popover>;

/** Выпадающее меню. Пункты закрывают его сами через popovertarget. */
export function Menu({ id, className, children, ...props }: MenuProps) {
  return (
    <MenuContext value={id}>
      <Popover
        id={id}
        role="menu"
        className={clsx(styles.menu, className)}
        {...props}
      >
        {children}
      </Popover>
    </MenuContext>
  );
}

interface MenuItemProps extends Omit<ComponentProps<'button'>, 'onSelect'> {
  icon?: LucideIcon;
  tone?: 'default' | 'danger';
  selected?: boolean;
  description?: ReactNode;
  trailing?: ReactNode;
  onSelect?: () => void;
  /** false — пункт-переключатель: меню остаётся открытым */
  closeOnSelect?: boolean;
}

export function MenuItem({
  icon: Icon,
  tone = 'default',
  selected = false,
  description,
  trailing,
  onSelect,
  closeOnSelect = true,
  className,
  children,
  ...props
}: MenuItemProps) {
  const menuId = use(MenuContext);

  return (
    <button
      type="button"
      role="menuitem"
      className={clsx(
        styles.item,
        styles[tone],
        selected && styles.selected,
        className,
      )}
      popoverTarget={(closeOnSelect && menuId) || undefined}
      popoverTargetAction="hide"
      onClick={onSelect}
      {...props}
    >
      {Icon && (
        <Icon
          className={styles.icon}
          size={description ? 18 : 16}
          aria-hidden
        />
      )}
      <span className={styles.text}>
        <span className={styles.label}>{children}</span>
        {description && (
          <span className={styles.description}>{description}</span>
        )}
      </span>
      {trailing}
    </button>
  );
}

export function MenuLabel({ children }: { children: ReactNode }) {
  return <div className={styles.groupLabel}>{children}</div>;
}

export function MenuSeparator() {
  return <hr className={styles.separator} />;
}
