import { ArrowUpRight } from 'lucide-react';
import { LoginForm } from '@features/login';
import { env } from '@shared/config/env';
import { Logo } from '@shared/ui/logo';
import styles from './LoginPage.module.scss';

export function LoginPage() {
  return (
    <main className={styles.page}>
      <div className={styles.card}>
        <Logo />
        <div className={styles.heading}>
          <h1 className={styles.title}>Вход в базу знаний</h1>
          <p className={styles.subtitle}>
            Используйте учётную запись DIOS — доступ к пространствам и статьям
            определяется вашими правами.
          </p>
        </div>
        <LoginForm />
        <a
          className={styles.dios}
          href={env.diosUrl}
          target="_blank"
          rel="noreferrer"
        >
          Открыть DIOS
          <ArrowUpRight size={14} aria-hidden />
        </a>
      </div>
    </main>
  );
}
