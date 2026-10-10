import type { Permission } from '@entities/access-grant';

/** Область знаний организации и верхний контекст доступа. */
export interface Space {
  id: string;
  createdAt: string;
  updatedAt: string;
  key: string;
  name: string;
  description: string | null;
  createdBy: string;
  permissions: Permission[];
}
