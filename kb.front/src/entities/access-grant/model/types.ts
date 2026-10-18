/** Права Knowledge (allow-only): итоговые права — объединение всех применимых grants. */
export type Permission = 'READ' | 'WRITE' | 'PUBLISH' | 'ARCHIVE';

export const PERMISSIONS: Permission[] = [
  'READ',
  'WRITE',
  'PUBLISH',
  'ARCHIVE',
];

export const PERMISSION_LABELS: Record<Permission, string> = {
  READ: 'Чтение',
  WRITE: 'Запись',
  PUBLISH: 'Публикация',
  ARCHIVE: 'Архивирование',
};

export type ResourceType = 'space' | 'collection' | 'article';
export type SubjectType = 'organization' | 'user' | 'role';

export interface Resource {
  type: ResourceType;
  id: string;
}

export interface Subject {
  type: SubjectType;
  id: string;
}

export interface AccessGrant {
  id: string;
  createdAt: string;
  grantedBy: string;
  resource: Resource;
  subject: Subject;
  permissions: Permission[];
}

/**
 * Эффективные права пришли с backend; UI по ним только скрывает действия.
 * Авторизацию всегда выполняет сервер.
 */
export function hasPermission(
  permissions: readonly Permission[] | undefined,
  required: Permission,
): boolean {
  return permissions?.includes(required) ?? false;
}
