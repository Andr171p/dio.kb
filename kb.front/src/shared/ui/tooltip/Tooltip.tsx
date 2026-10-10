import { useRef, type ReactNode } from 'react';
import { placeNear, type Placement } from '../popover';
import styles from './Tooltip.module.scss';

interface TooltipProps {
  label: ReactNode;
  placement?: Extract<Placement, 'top' | 'right-start'>;
  children: ReactNode;
}

export function Tooltip({ label, placement = 'top', children }: TooltipProps) {
  const anchorRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLSpanElement>(null);

  const show = () => {
    const tooltip = tooltipRef.current;
    if (!tooltip || !anchorRef.current || tooltip.matches(':popover-open'))
      return;

    tooltip.showPopover();
    placeNear(tooltip, anchorRef.current, placement);
  };

  const hide = () => {
    if (tooltipRef.current?.matches(':popover-open'))
      tooltipRef.current.hidePopover();
  };

  return (
    <span
      ref={anchorRef}
      className={styles.anchor}
      onPointerEnter={show}
      onPointerLeave={hide}
      onFocus={show}
      onBlur={hide}
      onClick={hide}
    >
      {children}
      <span
        ref={tooltipRef}
        role="tooltip"
        popover="manual"
        className={styles.tooltip}
      >
        {label}
      </span>
    </span>
  );
}
