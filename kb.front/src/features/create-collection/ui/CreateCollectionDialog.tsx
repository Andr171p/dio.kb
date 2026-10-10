import { useActionState } from 'react';
import { refreshNavigation, type Collection } from '@entities/collection';
import { ApiError, describeError, kbApi } from '@shared/api';
import { slugify } from '@shared/lib/slug';
import { Button } from '@shared/ui/button';
import { Dialog, DialogActions } from '@shared/ui/dialog';
import { TextAreaField, TextField } from '@shared/ui/field';
import { Notice } from '@shared/ui/notice';
import { toast } from '@shared/ui/toast';
import styles from './CreateCollectionDialog.module.scss';

interface CreateCollectionDialogProps {
  open: boolean;
  onClose: () => void;
  spaceId: string;
  /** Родительская коллекция; без неё — корневая */
  parent?: { id: string; title: string } | null;
}

const text = (form: FormData, name: string) => {
  const value = form.get(name);
  return typeof value === 'string' ? value.trim() : '';
};

export function CreateCollectionDialog({
  open,
  onClose,
  spaceId,
  parent,
}: CreateCollectionDialogProps) {
  const [error, submit, pending] = useActionState(
    async (_: string | null, form: FormData) => {
      const name = text(form, 'name');
      const create = (slug: string) =>
        kbApi.post<Collection>(`/api/user/v1/spaces/${spaceId}/collections`, {
          body: {
            name,
            slug,
            description: text(form, 'description') || undefined,
            parentId: parent?.id,
          },
        });

      try {
        const slug = slugify(name) || 'collection';
        await create(slug).catch((error: unknown) => {
          // Коллекция с таким slug уже есть: slug не виден пользователю, добавляем суффикс
          if (error instanceof ApiError && error.status === 409)
            return create(`${slug}-${Date.now().toString(36)}`);
          throw error;
        });
        await refreshNavigation(spaceId);
        toast.success(`Коллекция «${name}» создана`);
        onClose();
        return null;
      } catch (error) {
        return describeError(error);
      }
    },
    null,
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={parent ? 'Новая вложенная коллекция' : 'Новая коллекция'}
      description={
        parent
          ? `Коллекция появится внутри «${parent.title}».`
          : 'Коллекции помогают выстроить навигацию. Права на статьи они не меняют.'
      }
    >
      <form action={submit} className={styles.form}>
        {error && <Notice>{error}</Notice>}
        <TextField
          label="Название"
          name="name"
          required
          maxLength={255}
          autoFocus
        />
        <TextAreaField label="Описание" name="description" rows={2} />
        <DialogActions>
          <Button onClick={onClose}>Отмена</Button>
          <Button type="submit" variant="primary" loading={pending}>
            Создать
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
