import { useId, useRef } from 'react';

/**
 * Связывает кнопку-триггер и Popover: браузер сам открывает, закрывает
 * по клику снаружи и Esc, проставляет aria-expanded.
 */
export function usePopover() {
  const id = useId();
  const anchorRef = useRef<HTMLButtonElement>(null);

  return {
    triggerProps: { ref: anchorRef, popoverTarget: id },
    popoverProps: { id, anchorRef },
  };
}
