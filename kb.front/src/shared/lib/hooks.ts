import { useCallback, useEffect, useEffectEvent, useState } from 'react';

/**
 * Глобальное сочетание клавиш. `code` — физическая клавиша (KeyK),
 * поэтому сочетание работает при любой раскладке.
 */
export function useHotkey(
  code: string,
  handler: (event: KeyboardEvent) => void,
  { withModifier = false } = {},
) {
  const onHotkey = useEffectEvent(handler);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.code !== code) return;
      if (withModifier && !(event.ctrlKey || event.metaKey)) return;

      event.preventDefault();
      onHotkey(event);
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [code, withModifier]);
}

export function useCopyToClipboard(resetAfterMs = 1500) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), resetAfterMs);
    return () => clearTimeout(timer);
  }, [copied, resetAfterMs]);

  const copy = useCallback(async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
  }, []);

  return { copied, copy };
}

/** Значение, которое обновляется только после паузы `delayMs` — для поиска при вводе. */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(
    () => window.matchMedia(query).matches,
  );

  useEffect(() => {
    const media = window.matchMedia(query);
    const onChange = () => setMatches(media.matches);
    onChange();
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, [query]);

  return matches;
}

/** «⌘» на macOS, «Ctrl» на остальных системах — для подсказок сочетаний. */
export const MOD_KEY_LABEL = /Mac|iPhone|iPad/.test(navigator.platform)
  ? '⌘'
  : 'Ctrl';
