/** Учётная запись DIOS. */
export interface User {
  id: string;
  email: string;
  username: string | null;
  full_name: string | null;
  avatar_url: string | null;
  roles: string[];
}

export function displayName(
  user: Pick<User, 'email' | 'username' | 'full_name'>,
): string {
  return user.full_name ?? user.username ?? user.email;
}

/** Роль IAM `admin`: создаёт пространства и управляет доступом. Не обходит ACL. */
export function isAdmin(user: User | null): boolean {
  return user?.roles.includes('admin') ?? false;
}
