import { useActionState } from 'react';
import { useNavigate } from 'react-router';
import { upsertSpace, type Space } from '@entities/space';
import { describeError, kbApi } from '@shared/api';
import { routes } from '@shared/config/routes';
import { Button } from '@shared/ui/button';
import { Dialog, DialogActions } from '@shared/ui/dialog';
import { Checkbox, TextAreaField, TextField } from '@shared/ui/field';
import { Notice } from '@shared/ui/notice';
import { toast } from '@shared/ui/toast';
import styles from './CreateSpaceDialog.module.scss';

const KEY_PATTERN = '[A-Z][A-Z0-9_]{1,31}';

interface CreateSpaceDialogProps {
  open: boolean;
  onClose: () => void;
}

const text = (form: FormData, name: string) => {
  const value = form.get(name);
  return typeof value === 'string' ? value.trim() : '';
};

export function CreateSpaceDialog({ open, onClose }: CreateSpaceDialogProps) {
  const navigate = useNavigate();

  const [error, submit, pending] = useActionState(
    async (_: string | null, form: FormData) => {
      try {
        const space = await kbApi.post<Space>('/api/admin/v1/spaces', {
          body: {
            key: text(form, 'key'),
            name: text(form, 'name'),
            description: text(form, 'description') || undefined,
            organizationWide: form.get('organizationWide') === 'on',
          },
        });
        upsertSpace(space);
        toast.success(`Пространство «${space.name}» создано`);
        onClose();
        void navigate(routes.space(space.id));
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
      title="Новое пространство"
      description="Пространство — область знаний и граница доступа: права выдаются на него целиком."
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
        <TextField
          label="Ключ"
          name="key"
          required
          pattern={KEY_PATTERN}
          placeholder="ITSM"
          hint="Латиница в верхнем регистре, цифры и _, 2–32 символа"
          onInput={(event) => {
            const input = event.currentTarget;
            input.value = input.value.toUpperCase();
          }}
        />
        <TextAreaField label="Описание" name="description" rows={3} />
        <Checkbox
          name="organizationWide"
          defaultChecked
          label="Доступно всей организации"
          description="Все сотрудники получат право чтения. Иначе доступ — только по явным правам."
        />
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
