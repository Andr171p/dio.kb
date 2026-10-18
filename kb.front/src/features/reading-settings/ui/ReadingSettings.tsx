import type { RefObject } from 'react';
import { setTheme, useTheme, type Theme } from '@shared/lib/theme';
import { Button } from '@shared/ui/button';
import { Chip, ChipGroup } from '@shared/ui/chip';
import { Popover, usePopover } from '@shared/ui/popover';
import {
  changeTextSize,
  MAX_SIZE,
  MIN_SIZE,
  setLeading,
  useReadingSettings,
} from '../model/reading-settings';
import styles from './ReadingSettings.module.scss';

const THEMES: { value: Theme; label: string }[] = [
  { value: 'light', label: 'Светлая' },
  { value: 'dark', label: 'Тёмная' },
  { value: 'sepia', label: 'Сепия' },
];

export function TextSizeControl({
  compact = false,
  offset = 0,
}: {
  compact?: boolean;
  /** Поправка к показанному размеру: в режиме фокуса текст на 1 px крупнее */
  offset?: number;
}) {
  const size = useReadingSettings((state) => state.size);

  return (
    <div
      className={compact ? styles.sizeCompact : styles.size}
      role="group"
      aria-label="Размер текста"
    >
      <Button
        variant={compact ? 'ghost' : 'secondary'}
        size={compact ? 'sm' : 'md'}
        className={styles.sizeButton}
        aria-label="Уменьшить текст"
        disabled={size <= MIN_SIZE}
        onClick={() => changeTextSize(-1)}
      >
        A−
      </Button>
      <span className={styles.sizeValue} aria-live="polite">
        {size + offset} px
      </span>
      <Button
        variant={compact ? 'ghost' : 'secondary'}
        size={compact ? 'sm' : 'md'}
        className={styles.sizeButton}
        aria-label="Увеличить текст"
        disabled={size >= MAX_SIZE}
        onClick={() => changeTextSize(1)}
      >
        A+
      </Button>
    </div>
  );
}

/** Панель настроек чтения: размер и интервал текста, тема, режим фокуса. */
function ReadingSettingsPanel({ onFocusMode }: { onFocusMode?: () => void }) {
  const leading = useReadingSettings((state) => state.leading);
  const theme = useTheme((state) => state.theme);

  return (
    <div className={styles.panel}>
      <section>
        <h3 className={styles.label}>Размер текста</h3>
        <TextSizeControl />
      </section>
      <section>
        <h3 className={styles.label}>Межстрочный интервал</h3>
        <ChipGroup aria-label="Межстрочный интервал">
          <Chip
            selected={leading === 'normal'}
            className={styles.chip}
            onClick={() => setLeading('normal')}
          >
            Обычный
          </Chip>
          <Chip
            selected={leading === 'relaxed'}
            className={styles.chip}
            onClick={() => setLeading('relaxed')}
          >
            Свободный
          </Chip>
        </ChipGroup>
      </section>
      <section>
        <h3 className={styles.label}>Тема</h3>
        <ChipGroup aria-label="Тема">
          {THEMES.map((item) => (
            <Chip
              key={item.value}
              selected={theme === item.value}
              onClick={() => setTheme(item.value)}
            >
              {item.label}
            </Chip>
          ))}
        </ChipGroup>
      </section>
      {onFocusMode && (
        <Button block onClick={onFocusMode}>
          Включить фокус
        </Button>
      )}
    </div>
  );
}

interface ReadingSettingsButtonProps {
  onFocusMode?: () => void;
  className?: string;
  /** Короткая подпись «Aa» — для мобильной панели */
  compact?: boolean;
}

/** Кнопка «Aa Настройки чтения» с плавающей панелью. */
export function ReadingSettingsButton({
  onFocusMode,
  className,
  compact = false,
}: ReadingSettingsButtonProps) {
  const { triggerProps, popoverProps } = usePopover();

  return (
    <>
      <Button
        variant={compact ? 'ghost' : 'secondary'}
        size={compact ? 'sm' : 'md'}
        className={className}
        aria-label={compact ? 'Настройки чтения' : undefined}
        {...triggerProps}
      >
        <span className={styles.aa} aria-hidden>
          Aa
        </span>
        {!compact && 'Настройки чтения'}
      </Button>
      <Popover
        {...popoverProps}
        placement={compact ? 'top' : 'bottom-end'}
        className={styles.popover}
        aria-label="Настройки чтения"
      >
        <ReadingSettingsPanel onFocusMode={onFocusMode} />
      </Popover>
    </>
  );
}

interface ReadingSettingsPopoverProps {
  id: string;
  /** Куда прикрепить панель: например, к кнопке «⋯» в шапке */
  anchorRef: RefObject<HTMLElement | null>;
  onFocusMode?: () => void;
}

/** Панель настроек, открываемая программно — из пункта меню. */
export function ReadingSettingsPopover({
  id,
  anchorRef,
  onFocusMode,
}: ReadingSettingsPopoverProps) {
  return (
    <Popover
      id={id}
      anchorRef={anchorRef}
      placement="bottom-end"
      className={styles.popover}
      aria-label="Настройки чтения"
    >
      <ReadingSettingsPanel onFocusMode={onFocusMode} />
    </Popover>
  );
}
