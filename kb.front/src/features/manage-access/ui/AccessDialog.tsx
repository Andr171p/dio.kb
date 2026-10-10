import clsx from 'clsx';
import { Building2, Trash2, User, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import {
  PERMISSION_LABELS,
  PERMISSIONS,
  type AccessGrant,
  type Permission,
  type Resource,
  type SubjectType,
} from '@entities/access-grant';
import { userDisplayName, useUserName, type UserProfile } from '@entities/user';
import { describeError, isAbortError } from '@shared/api';
import { Button, IconButton } from '@shared/ui/button';
import { Dialog } from '@shared/ui/dialog';
import { SelectField, TextField } from '@shared/ui/field';
import { Notice } from '@shared/ui/notice';
import { Skeleton } from '@shared/ui/skeleton';
import { toast } from '@shared/ui/toast';
import {
  createGrant,
  listGrants,
  listUsers,
  revokeGrant,
  updateGrant,
} from '../model/grants';
import styles from './AccessDialog.module.scss';

interface AccessDialogProps {
  open: boolean;
  onClose: () => void;
  resource: Resource;
  title: string;
  /** Пространство ресурса: его права действуют на статьи и коллекции */
  spaceId?: string;
}

const RESOURCE_LABELS: Record<Resource['type'], string> = {
  space: 'пространству',
  collection: 'коллекции',
  article: 'статье',
};

function SubjectLabel({ grant }: { grant: AccessGrant }) {
  const userName = useUserName(
    grant.subject.type === 'user' ? grant.subject.id : null,
  );

  if (grant.subject.type === 'organization')
    return (
      <span className={styles.subject}>
        <Building2 size={15} aria-hidden /> Вся организация
      </span>
    );
  if (grant.subject.type === 'role')
    return (
      <span className={styles.subject}>
        <Users size={15} aria-hidden /> Роль{' '}
        <code className={styles.code}>{grant.subject.id}</code>
      </span>
    );
  return (
    <span className={styles.subject}>
      <User size={15} aria-hidden /> {userName ?? grant.subject.id}
    </span>
  );
}

interface PermissionTogglesProps {
  value: Permission[];
  disabled?: boolean;
  onChange?: (permissions: Permission[]) => void;
}

function PermissionToggles({
  value,
  disabled,
  onChange,
}: PermissionTogglesProps) {
  return (
    <div className={styles.toggles} role="group" aria-label="Права">
      {PERMISSIONS.map((permission) => {
        const active = value.includes(permission);
        return (
          <button
            key={permission}
            type="button"
            aria-pressed={active}
            disabled={disabled}
            className={clsx(styles.toggle, active && styles.toggleActive)}
            onClick={() => {
              const next = active
                ? value.filter((item) => item !== permission)
                : [...value, permission];
              // Без хотя бы одного права grant не имеет смысла — для этого есть «Отозвать»
              if (next.length > 0) onChange?.(next);
            }}
          >
            {PERMISSION_LABELS[permission]}
          </button>
        );
      })}
    </div>
  );
}

function GrantRow({
  grant,
  onChange,
  onRevoke,
}: {
  grant: AccessGrant;
  onChange: (grant: AccessGrant) => void;
  onRevoke: (grantId: string) => void;
}) {
  const [pending, setPending] = useState(false);

  const update = async (permissions: Permission[]) => {
    setPending(true);
    try {
      onChange(await updateGrant(grant.id, permissions));
    } catch (error) {
      toast.error(describeError(error));
    } finally {
      setPending(false);
    }
  };

  const revoke = async () => {
    setPending(true);
    try {
      await revokeGrant(grant.id);
      onRevoke(grant.id);
    } catch (error) {
      toast.error(describeError(error));
      setPending(false);
    }
  };

  return (
    <li className={styles.row}>
      <SubjectLabel grant={grant} />
      <PermissionToggles
        value={grant.permissions}
        disabled={pending}
        onChange={(permissions) => void update(permissions)}
      />
      <IconButton
        icon={Trash2}
        label="Отозвать доступ"
        disabled={pending}
        onClick={() => void revoke()}
      />
    </li>
  );
}

function AddGrantForm({
  resource,
  onCreated,
}: {
  resource: Resource;
  onCreated: (grant: AccessGrant) => void;
}) {
  const [subjectType, setSubjectType] =
    useState<Exclude<SubjectType, 'organization'>>('user');
  const [subjectId, setSubjectId] = useState('');
  const [permissions, setPermissions] = useState<Permission[]>(['READ']);
  const [users, setUsers] = useState<UserProfile[] | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (subjectType !== 'user' || users) return;
    const controller = new AbortController();
    listUsers(controller.signal)
      .then(setUsers)
      .catch((error: unknown) => {
        if (!isAbortError(error)) setUsers([]);
      });
    return () => controller.abort();
  }, [subjectType, users]);

  const submit = async () => {
    const id = subjectId.trim();
    if (!id) return;
    setPending(true);
    try {
      onCreated(
        await createGrant(resource, { type: subjectType, id }, permissions),
      );
      setSubjectId('');
      toast.success('Доступ выдан');
    } catch (error) {
      toast.error(describeError(error));
    } finally {
      setPending(false);
    }
  };

  return (
    <form
      className={styles.addForm}
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <div className={styles.addRow}>
        <SelectField
          label="Кому"
          value={subjectType}
          className={styles.typeField}
          onChange={(event) => {
            setSubjectType(event.target.value as 'user' | 'role');
            setSubjectId('');
          }}
        >
          <option value="user">Пользователь</option>
          <option value="role">Роль DIOS</option>
        </SelectField>
        {subjectType === 'user' ? (
          <SelectField
            label="Пользователь"
            value={subjectId}
            required
            className={styles.subjectField}
            onChange={(event) => setSubjectId(event.target.value)}
          >
            <option value="" disabled>
              {users ? 'Выберите пользователя' : 'Загрузка…'}
            </option>
            {users?.map((user) => (
              <option key={user.id} value={user.id}>
                {userDisplayName(user)} · {user.email}
              </option>
            ))}
          </SelectField>
        ) : (
          <TextField
            label="Код роли"
            value={subjectId}
            required
            placeholder="support_agent"
            className={styles.subjectField}
            onChange={(event) => setSubjectId(event.target.value)}
          />
        )}
      </div>
      <div className={styles.addRow}>
        <PermissionToggles value={permissions} onChange={setPermissions} />
        <Button
          type="submit"
          variant="primary"
          loading={pending}
          disabled={!subjectId}
        >
          Выдать доступ
        </Button>
      </div>
    </form>
  );
}

/** Права на пространство, коллекцию или статью. Доступно администраторам. */
export function AccessDialog({
  open,
  onClose,
  resource,
  title,
  spaceId,
}: AccessDialogProps) {
  const [grants, setGrants] = useState<AccessGrant[] | null>(null);
  const [inherited, setInherited] = useState<AccessGrant[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    // Диалог монтируется заново при каждом открытии — начальное состояние уже «загрузка»
    const controller = new AbortController();

    const spaceResource =
      spaceId && resource.type !== 'space'
        ? ({ type: 'space', id: spaceId } as const)
        : null;

    Promise.all([
      listGrants(resource, controller.signal),
      spaceResource ? listGrants(spaceResource, controller.signal) : [],
    ])
      .then(([own, fromSpace]) => {
        setGrants(own);
        setInherited(fromSpace);
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) setError(describeError(error));
      });

    return () => controller.abort();
  }, [open, resource, spaceId]);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      size="md"
      title="Доступ"
      description={`Права по ${RESOURCE_LABELS[resource.type]} «${title}». Права объединяются: запретить доступ, выданный на пространство, нельзя.`}
    >
      {error && <Notice>{error}</Notice>}

      {grants === null && !error ? (
        <div className={styles.loading}>
          <Skeleton height={40} />
          <Skeleton height={40} />
        </div>
      ) : (
        grants && (
          <ul className={styles.list}>
            {grants.length === 0 && (
              <li className={styles.empty}>Явных прав пока нет.</li>
            )}
            {grants.map((grant) => (
              <GrantRow
                key={grant.id}
                grant={grant}
                onChange={(updated) =>
                  setGrants(
                    (items) =>
                      items?.map((item) =>
                        item.id === updated.id ? updated : item,
                      ) ?? null,
                  )
                }
                onRevoke={(grantId) =>
                  setGrants(
                    (items) =>
                      items?.filter((item) => item.id !== grantId) ?? null,
                  )
                }
              />
            ))}
          </ul>
        )
      )}

      {inherited.length > 0 && (
        <section className={styles.inherited}>
          <h3 className={styles.sectionTitle}>Действуют через пространство</h3>
          <ul className={styles.list}>
            {inherited.map((grant) => (
              <li key={grant.id} className={clsx(styles.row, styles.readonly)}>
                <SubjectLabel grant={grant} />
                <PermissionToggles value={grant.permissions} disabled />
              </li>
            ))}
          </ul>
        </section>
      )}

      {grants && (
        <section>
          <h3 className={styles.sectionTitle}>Выдать доступ</h3>
          <AddGrantForm
            resource={resource}
            onCreated={(grant) =>
              setGrants((items) => [...(items ?? []), grant])
            }
          />
        </section>
      )}
    </Dialog>
  );
}
