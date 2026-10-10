import { useActionState } from 'react';
import { Button } from '@shared/ui/button';
import { Dialog, DialogActions } from '@shared/ui/dialog';
import { TextField } from '@shared/ui/field';
import { toast } from '@shared/ui/toast';
import { renameCollection } from '../model/collection-actions';
import styles from './ManageCollection.module.scss';

interface RenameCollectionDialogProps {
  open: boolean;
  onClose: () => void;
  spaceId: string;
  collection: { id: string; title: string };
}

export function RenameCollectionDialog({
  open,
  onClose,
  spaceId,
  collection,
}: RenameCollectionDialogProps) {
  const [, submit, pending] = useActionState(
    async (_: null, form: FormData) => {
      const value = form.get('name');
      const name = typeof value === 'string' ? value.trim() : '';
      try {
        await renameCollection(spaceId, collection.id, { name });
        toast.success('Коллекция переименована');
        onClose();
      } catch {
        // Ошибку уже показал тост
      }
      return null;
    },
    null,
  );

  return (
    <Dialog open={open} onClose={onClose} title="Переименовать коллекцию">
      <form action={submit} className={styles.form}>
        <TextField
          label="Название"
          name="name"
          defaultValue={collection.title}
          required
          maxLength={255}
          autoFocus
        />
        <DialogActions>
          <Button onClick={onClose}>Отмена</Button>
          <Button type="submit" variant="primary" loading={pending}>
            Сохранить
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
