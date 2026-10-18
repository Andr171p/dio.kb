import { useActionState } from 'react';
import { login } from '@entities/session';
import { ApiError, describeError } from '@shared/api';
import { Button } from '@shared/ui/button';
import { TextField } from '@shared/ui/field';
import { Notice } from '@shared/ui/notice';
import styles from './LoginForm.module.scss';

interface LoginState {
  email: string;
  error: string | null;
}

const field = (form: FormData, name: string) => {
  const value = form.get(name);
  return typeof value === 'string' ? value : '';
};

async function submit(_: LoginState, form: FormData): Promise<LoginState> {
  const email = field(form, 'email').trim();
  const password = field(form, 'password');

  try {
    await login(email, password);
    return { email, error: null };
  } catch (error) {
    const message =
      error instanceof ApiError && error.status === 401
        ? 'Неверный email или пароль'
        : describeError(error);
    return { email, error: message };
  }
}

export function LoginForm() {
  const [state, action, pending] = useActionState(submit, {
    email: '',
    error: null,
  });

  return (
    <form action={action} className={styles.form}>
      {state.error && <Notice>{state.error}</Notice>}
      <TextField
        label="Email"
        name="email"
        type="email"
        autoComplete="username"
        defaultValue={state.email}
        required
        autoFocus
      />
      <TextField
        label="Пароль"
        name="password"
        type="password"
        autoComplete="current-password"
        required
      />
      <Button
        type="submit"
        variant="primary"
        loading={pending}
        className={styles.submit}
      >
        Войти
      </Button>
    </form>
  );
}
