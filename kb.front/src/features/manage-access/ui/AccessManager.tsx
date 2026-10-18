import { Building2, Trash2, User, Users } from 'lucide-react';
import { useEffect, useId, useMemo, useState } from 'react';
import {
  PERMISSION_LABELS,
  PERMISSIONS,
  type AccessGrant,
  type Permission,
  type Resource,
  type Subject,
} from '@entities/access-grant';
import { userDisplayName, useUserName, type UserProfile } from '@entities/user';
import { describeError, isAbortError } from '@shared/api';
import { IconButton } from '@shared/ui/button';
import { Callout } from '@shared/ui/callout';
import { Chip, ChipGroup } from '@shared/ui/chip';
import { Notice } from '@shared/ui/notice';
import { SearchField } from '@shared/ui/search-field';
import { Skeleton } from '@shared/ui/skeleton';
import { toast } from '@shared/ui/toast';
import {
  createGrant,
  listGrants,
  listUsers,
  revokeGrant,
  updateGrant,
} from '../model/grants';
import styles from './AccessManager.module.scss';

const SUGGESTION_LIMIT = 6;

function SubjectName({ grant }: { grant: AccessGrant }) {
  const userName = useUserName(
    grant.subject.type === 'user' ? grant.subject.id : null,
  );

  if (grant.subject.type === 'organization')
    return (
      <span className={styles.subject}>
        <Building2 size={17} aria-hidden /> Вся организация
      </span>
    );
  if (grant.subject.type === 'role')
    return (
      <span className={styles.subject}>
        <Users size={17} aria-hidden /> Роль {grant.subject.id}
      </span>
    );
  return (
    <span className={styles.subject}>
      <User size={17} aria-hidden /> {userName ?? '…'}
    </span>
  );
}

function permissionsText(permissions: Permission[]): string {
  return PERMISSIONS.filter((permission) => permissions.includes(permission))
    .map((permission) => PERMISSION_LABELS[permission])
    .join(' · ');
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
    <tr>
      <td>
        <SubjectName grant={grant} />
      </td>
      <td>
        <ChipGroup aria-label="Разрешения" className={styles.toggles}>
          {PERMISSIONS.map((permission) => {
            const active = grant.permissions.includes(permission);
            return (
              <Chip
                key={permission}
                selected={active}
                disabled={pending}
                className={styles.toggle}
                onClick={() => {
                  const next = active
                    ? grant.permissions.filter((item) => item !== permission)
                    : [...grant.permissions, permission];
                  // Без хотя бы одного права grant не имеет смысла — для этого есть «Отозвать»
                  if (next.length > 0) void update(next);
                }}
              >
                {PERMISSION_LABELS[permission]}
              </Chip>
            );
          })}
        </ChipGroup>
      </td>
      <td className={styles.source}>
        <span>Прямой доступ</span>
        <IconButton
          icon={Trash2}
          label="Отозвать доступ"
          disabled={pending}
          onClick={() => void revoke()}
        />
      </td>
    </tr>
  );
}

interface Suggestion {
  key: string;
  label: string;
  meta: string;
  subject: Subject;
}

/** Выдача доступа: поиск пользователя DIOS или код роли. Новый доступ — с правом чтения. */
function AddGrant({
  resource,
  existing,
  onCreated,
}: {
  resource: Resource;
  existing: AccessGrant[];
  onCreated: (grant: AccessGrant) => void;
}) {
  const listId = useId();
  const [query, setQuery] = useState('');
  const [users, setUsers] = useState<UserProfile[] | null>(null);
  const [active, setActive] = useState(0);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    listUsers(controller.signal)
      .then(setUsers)
      .catch((error: unknown) => {
        if (!isAbortError(error)) setUsers([]);
      });
    return () => controller.abort();
  }, []);

  const suggestions = useMemo<Suggestion[]>(() => {
    const term = query.trim().toLocaleLowerCase('ru');
    if (!term) return [];
    const granted = new Set(
      existing.map((grant) => `${grant.subject.type}:${grant.subject.id}`),
    );
    const matches: Suggestion[] = (users ?? [])
      .filter(
        (user) =>
          !granted.has(`user:${user.id}`) &&
          `${userDisplayName(user)} ${user.email}`
            .toLocaleLowerCase('ru')
            .includes(term),
      )
      .slice(0, SUGGESTION_LIMIT)
      .map((user) => ({
        key: `user:${user.id}`,
        label: userDisplayName(user),
        meta: user.email,
        subject: { type: 'user', id: user.id },
      }));
    // Код роли DIOS: латиница, цифры и подчёркивание
    if (/^[a-z][a-z0-9_]*$/.test(term) && !granted.has(`role:${term}`))
      matches.push({
        key: `role:${term}`,
        label: `Роль ${term}`,
        meta: 'Все пользователи DIOS с этой ролью',
        subject: { type: 'role', id: term },
      });
    return matches;
  }, [query, users, existing]);

  const add = async (suggestion: Suggestion) => {
    setPending(true);
    try {
      onCreated(await createGrant(resource, suggestion.subject, ['READ']));
      setQuery('');
      toast.success(`Доступ выдан: ${suggestion.label}`);
    } catch (error) {
      toast.error(describeError(error));
    } finally {
      setPending(false);
    }
  };

  const current = Math.min(active, Math.max(suggestions.length - 1, 0));

  return (
    <div className={styles.add}>
      <SearchField
        value={query}
        placeholder="Добавить пользователя или роль"
        aria-label="Добавить пользователя или роль"
        role="combobox"
        aria-expanded={suggestions.length > 0}
        aria-controls={listId}
        aria-activedescendant={
          suggestions.length ? `${listId}-${current}` : undefined
        }
        disabled={pending}
        onChange={(event) => {
          setQuery(event.target.value);
          setActive(0);
        }}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            const delta = event.key === 'ArrowDown' ? 1 : -1;
            setActive(
              (current + delta + suggestions.length) %
                Math.max(suggestions.length, 1),
            );
          } else if (event.key === 'Enter' && suggestions[current]) {
            event.preventDefault();
            void add(suggestions[current]);
          } else if (event.key === 'Escape') setQuery('');
        }}
      />
      {query.trim() && (
        <ul id={listId} role="listbox" className={styles.suggestions}>
          {suggestions.length === 0 && (
            <li className={styles.noMatch}>
              {users === null
                ? 'Загружаем пользователей…'
                : 'Никого не нашли. Для роли введите её код, например support_agent.'}
            </li>
          )}
          {suggestions.map((suggestion, index) => (
            <li
              key={suggestion.key}
              id={`${listId}-${index}`}
              role="option"
              aria-selected={index === current}
              className={styles.suggestion}
              data-active={index === current || undefined}
              onPointerMove={() => setActive(index)}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => void add(suggestion)}
            >
              <span className={styles.suggestionLabel}>{suggestion.label}</span>
              <span className={styles.suggestionMeta}>{suggestion.meta}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const RESOURCE_HINTS: Record<Resource['type'], string> = {
  space:
    'Права пространства действуют на все его коллекции и статьи. Сузить их на отдельной статье нельзя.',
  collection:
    'Коллекции задают навигацию. Права на коллекцию не открывают её статьи — права статьи проверяются отдельно.',
  article: 'Коллекции задают навигацию. Права статьи проверяются отдельно.',
};

interface AccessManagerProps {
  resource: Resource;
  /** Пространство ресурса: его права действуют на статьи и коллекции */
  space?: { id: string; name: string };
}

/** Права на пространство, коллекцию или статью. Итог проверяет сервер. */
export function AccessManager({ resource, space }: AccessManagerProps) {
  const [grants, setGrants] = useState<AccessGrant[] | null>(null);
  const [inherited, setInherited] = useState<AccessGrant[]>([]);
  const [error, setError] = useState<string | null>(null);
  const spaceId = space?.id;

  useEffect(() => {
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
        setError(null);
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) setError(describeError(error));
      });

    return () => controller.abort();
  }, [resource, spaceId]);

  return (
    <div className={styles.manager}>
      <Callout
        title={
          resource.type === 'space'
            ? 'Доступ ко всему пространству'
            : `Доступ через пространство «${space?.name ?? '…'}»`
        }
      >
        {RESOURCE_HINTS[resource.type]}
      </Callout>

      {grants && (
        <AddGrant
          resource={resource}
          existing={grants}
          onCreated={(grant) => setGrants((items) => [...(items ?? []), grant])}
        />
      )}

      {error && <Notice>{error}</Notice>}

      {grants === null && !error ? (
        <div className={styles.loading}>
          <Skeleton height={48} />
          <Skeleton height={48} />
        </div>
      ) : (
        grants && (
          <table className={styles.table}>
            <thead>
              <tr>
                <th scope="col">Пользователь</th>
                <th scope="col">Разрешения</th>
                <th scope="col">Источник</th>
              </tr>
            </thead>
            <tbody>
              {inherited.map((grant) => (
                <tr key={grant.id} className={styles.inherited}>
                  <td>
                    <SubjectName grant={grant} />
                  </td>
                  <td>{permissionsText(grant.permissions)}</td>
                  <td className={styles.source}>Пространство</td>
                </tr>
              ))}
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
              {grants.length === 0 && inherited.length === 0 && (
                <tr>
                  <td colSpan={3} className={styles.empty}>
                    Явных прав пока нет.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )
      )}
    </div>
  );
}
