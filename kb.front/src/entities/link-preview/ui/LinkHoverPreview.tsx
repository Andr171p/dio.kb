import { useRef, useState, type ReactElement, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { placeNear } from '@shared/ui/popover';
import { useLinkPreview } from '../model/link-previews-store';
import { LinkPreviewBody } from './LinkPreviewCard';
import styles from './LinkHoverPreview.module.scss';

const OPEN_DELAY_MS = 400;
const CLOSE_DELAY_MS = 180;

interface LinkHoverPreviewProps {
  href: string;
  children: ReactNode;
}

/**
 * Всплывающее превью ссылки при наведении или фокусе.
 * Превью грузится только после задержки, чтобы не дёргать API при проведении курсора.
 */
export function LinkHoverPreview({
  href,
  children,
}: LinkHoverPreviewProps): ReactElement {
  const anchorRef = useRef<HTMLSpanElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const [active, setActive] = useState(false);
  const preview = useLinkPreview(href, active);

  const open = () => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      const card = cardRef.current;
      if (!card || !anchorRef.current) return;
      setActive(true);
      if (!card.matches(':popover-open')) card.showPopover();
      placeNear(card, anchorRef.current, 'bottom-start');
    }, OPEN_DELAY_MS);
  };

  const close = () => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      if (cardRef.current?.matches(':popover-open'))
        cardRef.current.hidePopover();
    }, CLOSE_DELAY_MS);
  };

  return (
    <span
      ref={anchorRef}
      className={styles.anchor}
      onPointerEnter={open}
      onPointerLeave={close}
      onFocus={open}
      onBlur={close}
    >
      {children}
      {/* В body: ссылка стоит внутри абзаца, а в абзаце не может быть блоков */}
      {createPortal(
        <div
          ref={cardRef}
          popover="manual"
          className={styles.card}
          onPointerEnter={() => clearTimeout(timer.current)}
          onPointerLeave={close}
        >
          {active && <LinkPreviewBody href={href} preview={preview} />}
        </div>,
        document.body,
      )}
    </span>
  );
}
