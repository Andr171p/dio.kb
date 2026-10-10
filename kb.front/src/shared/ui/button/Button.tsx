import clsx from 'clsx';
import type { LucideIcon } from 'lucide-react';
import type { ComponentProps } from 'react';
import { Link } from 'react-router';
import { Spinner } from '../spinner';
import { Tooltip } from '../tooltip';
import styles from './Button.module.scss';

export const SOON_LABEL = 'Скоро';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
type Size = 'md' | 'sm';

interface ButtonProps extends ComponentProps<'button'> {
  variant?: Variant;
  size?: Size;
  icon?: LucideIcon;
  loading?: boolean;
  /** Функция ещё не поддерживается API: кнопка неактивна и объясняет это подсказкой */
  soon?: boolean;
  block?: boolean;
}

export function Button({
  variant = 'secondary',
  size = 'md',
  icon: Icon,
  loading = false,
  soon = false,
  block = false,
  disabled,
  type = 'button',
  className,
  children,
  onClick,
  ...props
}: ButtonProps) {
  const button = (
    <button
      type={type}
      className={clsx(
        styles.button,
        styles[variant],
        styles[size],
        block && styles.block,
        className,
      )}
      disabled={disabled || loading}
      aria-disabled={soon || undefined}
      aria-busy={loading || undefined}
      onClick={soon ? undefined : onClick}
      {...props}
    >
      {loading ? <Spinner /> : Icon && <Icon size={16} aria-hidden />}
      {children}
    </button>
  );

  return soon ? <Tooltip label={SOON_LABEL}>{button}</Tooltip> : button;
}

interface IconButtonProps extends Omit<ComponentProps<'button'>, 'children'> {
  icon: LucideIcon;
  /** Подпись для скринридеров и подсказки */
  label: string;
  variant?: Variant;
  size?: Size;
  soon?: boolean;
  tooltip?: boolean;
  tooltipPlacement?: 'top' | 'right-start';
}

export function IconButton({
  icon: Icon,
  label,
  variant = 'ghost',
  size = 'sm',
  soon = false,
  tooltip = true,
  tooltipPlacement,
  type = 'button',
  className,
  onClick,
  ...props
}: IconButtonProps) {
  const fullLabel = soon ? `${label} · ${SOON_LABEL.toLowerCase()}` : label;

  const button = (
    <button
      type={type}
      className={clsx(
        styles.button,
        styles.icon,
        styles[variant],
        styles[size],
        className,
      )}
      aria-label={fullLabel}
      aria-disabled={soon || undefined}
      onClick={soon ? undefined : onClick}
      {...props}
    >
      <Icon size={size === 'sm' ? 16 : 18} aria-hidden />
    </button>
  );

  return tooltip ? (
    <Tooltip label={fullLabel} placement={tooltipPlacement}>
      {button}
    </Tooltip>
  ) : (
    button
  );
}

interface ButtonLinkProps extends ComponentProps<typeof Link> {
  variant?: Variant;
  size?: Size;
  icon?: LucideIcon;
}

/** Ссылка, оформленная кнопкой: для навигации вместо вложения кнопки в ссылку. */
export function ButtonLink({
  variant = 'secondary',
  size = 'md',
  icon: Icon,
  className,
  children,
  ...props
}: ButtonLinkProps) {
  return (
    <Link
      className={clsx(
        styles.button,
        styles[variant],
        styles[size],
        styles.link,
        className,
      )}
      {...props}
    >
      {Icon && <Icon size={16} aria-hidden />}
      {children}
    </Link>
  );
}
