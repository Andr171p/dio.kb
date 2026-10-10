import clsx from 'clsx';
import {
  useEffect,
  useEffectEvent,
  useRef,
  type ComponentProps,
  type RefObject,
} from 'react';
import styles from './Popover.module.scss';
import { placeNear, type Placement } from './placement';

interface PopoverProps extends Omit<ComponentProps<'div'>, 'popover'> {
  id: string;
  anchorRef: RefObject<HTMLElement | null>;
  placement?: Placement;
  onOpenChange?: (open: boolean) => void;
}

export function Popover({
  id,
  anchorRef,
  placement = 'bottom-start',
  onOpenChange,
  className,
  children,
  ...props
}: PopoverProps) {
  const ref = useRef<HTMLDivElement>(null);

  const onBeforeToggle = useEffectEvent((event: ToggleEvent) => {
    if (event.newState === 'open' && ref.current && anchorRef.current) {
      placeNear(ref.current, anchorRef.current, placement);
    }
    onOpenChange?.(event.newState === 'open');
  });

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const listener = (event: Event) => onBeforeToggle(event as ToggleEvent);
    element.addEventListener('beforetoggle', listener);
    return () => element.removeEventListener('beforetoggle', listener);
  }, []);

  return (
    <div
      ref={ref}
      id={id}
      popover="auto"
      className={clsx(styles.popover, className)}
      {...props}
    >
      {children}
    </div>
  );
}
