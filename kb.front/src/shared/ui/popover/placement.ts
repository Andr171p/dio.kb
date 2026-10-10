export type Placement =
  | 'top'
  | 'top-start'
  | 'top-end'
  | 'bottom-start'
  | 'bottom-end'
  | 'right-start'
  | 'right-end';

const GAP = 8;
const VIEWPORT_PADDING = 8;

/**
 * Позиционирует элемент из top layer относительно якоря.
 * Не требует размеров самого элемента, поэтому работает до его отрисовки (beforetoggle).
 */
export function placeNear(
  element: HTMLElement,
  anchor: HTMLElement,
  placement: Placement,
) {
  const rect = anchor.getBoundingClientRect();
  const { clientWidth: width, clientHeight: height } = document.documentElement;
  const [side, align] = placement.split('-');
  const style = element.style;

  style.inset = 'auto';

  if (side === 'right') {
    style.left = `${rect.right + GAP}px`;
    if (align === 'end') style.bottom = `${height - rect.bottom}px`;
    else style.top = `${rect.top}px`;
    return;
  }

  if (side === 'top') {
    style.bottom = `${height - rect.top + GAP}px`;
    style.maxHeight = `${rect.top - GAP - VIEWPORT_PADDING}px`;
  } else {
    style.top = `${rect.bottom + GAP}px`;
    style.maxHeight = `${height - rect.bottom - GAP - VIEWPORT_PADDING}px`;
  }

  if (align === 'start') style.left = `${rect.left}px`;
  else if (align === 'end') style.right = `${width - rect.right}px`;
  else {
    // По центру: здесь элемент уже отрисован, поэтому ширину можно измерить
    const left = rect.left + rect.width / 2 - element.offsetWidth / 2;
    style.left = `${Math.min(Math.max(left, VIEWPORT_PADDING), width - element.offsetWidth - VIEWPORT_PADDING)}px`;
  }
}
