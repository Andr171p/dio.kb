import type {
  AccessGrant,
  Permission,
  Resource,
  Subject,
} from '@entities/access-grant';
import { diosApi, kbApi } from '@shared/api';
import type { UserProfile } from '@entities/user';

const GRANTS = '/api/admin/v1/access/grants';

export function listGrants(
  resource: Resource,
  signal?: AbortSignal,
): Promise<AccessGrant[]> {
  return kbApi.get<AccessGrant[]>(GRANTS, {
    query: { resourceType: resource.type, resourceId: resource.id },
    signal,
  });
}

export function createGrant(
  resource: Resource,
  subject: Subject,
  permissions: Permission[],
): Promise<AccessGrant> {
  return kbApi.post<AccessGrant>(GRANTS, {
    body: { resource, subject, permissions },
  });
}

export function updateGrant(
  grantId: string,
  permissions: Permission[],
): Promise<AccessGrant> {
  return kbApi.patch<AccessGrant>(`${GRANTS}/${grantId}`, {
    body: { permissions },
  });
}

export function revokeGrant(grantId: string): Promise<void> {
  return kbApi.delete(`${GRANTS}/${grantId}`);
}

interface UsersPage {
  items: UserProfile[];
}

/** Пользователи DIOS для выбора субъекта. В IAM пока нет поиска — берём первую страницу. */
export async function listUsers(signal?: AbortSignal): Promise<UserProfile[]> {
  const { items } = await diosApi.get<UsersPage>('/api/v1/users', {
    query: { page: 1, size: 100 },
    signal,
  });
  return items;
}
