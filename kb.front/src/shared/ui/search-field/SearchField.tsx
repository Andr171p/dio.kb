import clsx from 'clsx';
import { Search } from 'lucide-react';
import type { ComponentProps, ReactNode } from 'react';
import { Kbd } from '../kbd';
import styles from './SearchField.module.scss';

interface SearchFieldProps extends Omit<ComponentProps<'input'>, 'size'> {
  /** Подсказка сочетания клавиш справа, например `['Ctrl', 'K']` */
  shortcut?: string[];
  /** Содержимое справа вместо подсказки: спиннер, кнопка очистки */
  trailing?: ReactNode;
  containerClassName?: string;
}

/** Основное поле поиска 64 px: главная, поиск, пространство, выдача доступа. */
export function SearchField({
  shortcut,
  trailing,
  containerClassName,
  className,
  ...props
}: SearchFieldProps) {
  return (
    <div className={clsx(styles.field, containerClassName)}>
      <Search size={22} strokeWidth={1.6} className={styles.icon} aria-hidden />
      <input
        type="search"
        className={clsx(styles.input, className)}
        autoComplete="off"
        {...props}
      />
      {trailing}
      {shortcut && <Kbd keys={shortcut} className={styles.kbd} />}
    </div>
  );
}
