import clsx from 'clsx';
import type { ComponentProps } from 'react';
import styles from './Chip.module.scss';

interface ChipProps extends ComponentProps<'button'> {
  /** Выбранный фильтр или вариант: акцентный фон */
  selected?: boolean;
}

/** Чип-переключатель 30 px: фильтры поиска, вкладки истории, настройки чтения. */
export function Chip({
  selected = false,
  type = 'button',
  className,
  ...props
}: ChipProps) {
  return (
    <button
      type={type}
      aria-pressed={selected}
      className={clsx(styles.chip, selected && styles.selected, className)}
      {...props}
    />
  );
}

/** Группа чипов в строку с переносом. */
export function ChipGroup({ className, ...props }: ComponentProps<'div'>) {
  return (
    <div role="group" className={clsx(styles.group, className)} {...props} />
  );
}
