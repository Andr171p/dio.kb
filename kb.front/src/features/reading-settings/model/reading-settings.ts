import type { CSSProperties } from 'react';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Leading = 'normal' | 'relaxed';

interface ReadingSettings {
  /** Размер основного текста статьи, px */
  size: number;
  leading: Leading;
}

export const MIN_SIZE = 15;
export const MAX_SIZE = 24;
const DEFAULT_SIZE = 18;

const LEADING: Record<Leading, number> = { normal: 1.65, relaxed: 1.85 };

/** Настройки чтения — удобство конкретного браузера, не данные пользователя. */
export const useReadingSettings = create<ReadingSettings>()(
  persist((): ReadingSettings => ({ size: DEFAULT_SIZE, leading: 'normal' }), {
    name: 'dios.kb.reading',
  }),
);

export function changeTextSize(delta: number) {
  useReadingSettings.setState(({ size }) => ({
    size: Math.min(MAX_SIZE, Math.max(MIN_SIZE, size + delta)),
  }));
}

export function setLeading(leading: Leading) {
  useReadingSettings.setState({ leading });
}

/** CSS-переменные типографики статьи: подхватываются `prose` через `--text-body`. */
export function useReadingStyle(sizeOffset = 0): CSSProperties {
  const size = useReadingSettings((state) => state.size);
  const leading = useReadingSettings((state) => state.leading);
  return {
    '--reading-size': `${size + sizeOffset}px`,
    '--reading-leading': LEADING[leading],
  } as CSSProperties;
}
