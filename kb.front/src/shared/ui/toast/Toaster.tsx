import clsx from 'clsx';
import { CircleAlert, CircleCheck, Info, X } from 'lucide-react';
import { dismissToast, useToasts } from './toast-store';
import styles from './Toaster.module.scss';

const ICONS = { success: CircleCheck, error: CircleAlert, info: Info };

export function Toaster() {
  const items = useToasts((state) => state.items);

  return (
    <div className={styles.region} role="region" aria-label="Уведомления">
      {items.map((item) => {
        const Icon = ICONS[item.tone];
        return (
          <div
            key={item.id}
            role={item.tone === 'error' ? 'alert' : 'status'}
            className={clsx(styles.toast, styles[item.tone])}
          >
            <Icon size={16} className={styles.icon} aria-hidden />
            <span className={styles.message}>{item.message}</span>
            <button
              type="button"
              className={styles.close}
              aria-label="Скрыть"
              onClick={() => dismissToast(item.id)}
            >
              <X size={14} aria-hidden />
            </button>
          </div>
        );
      })}
    </div>
  );
}
