import { useState } from 'react';
import { Button } from '../button';
import { Dialog, DialogActions } from './Dialog';
import { useConfirm } from './confirm-store';

/** Монтируется один раз в корне приложения. */
export function ConfirmHost() {
  const options = useConfirm((state) => state.options);
  const [pending, setPending] = useState(false);
  const close = () => useConfirm.setState({ options: null });

  const confirm = async () => {
    if (!options) return;
    setPending(true);
    try {
      await options.onConfirm();
      close();
    } catch {
      // Ошибку показывает сам обработчик; диалог остаётся открытым для повтора
    } finally {
      setPending(false);
    }
  };

  return (
    <Dialog
      open={options !== null}
      onClose={close}
      title={options?.title ?? ''}
      description={options?.description}
    >
      <DialogActions>
        <Button onClick={close} disabled={pending}>
          Отмена
        </Button>
        <Button
          variant={options?.tone === 'danger' ? 'danger' : 'primary'}
          loading={pending}
          onClick={() => void confirm()}
          autoFocus
        >
          {options?.confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
