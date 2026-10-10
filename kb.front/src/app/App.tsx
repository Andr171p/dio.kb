import { RouterProvider } from 'react-router/dom';
import { restoreSession, useSession } from '@entities/session';
import { LoginPage } from '@pages/login';
import { router } from './router';
import { SplashScreen } from './ui/SplashScreen';

export function App() {
  const status = useSession((state) => state.status);
  const restoreError = useSession((state) => state.restoreError);

  // Адрес не меняется: после входа пользователь попадает туда, куда шёл
  if (status === 'anonymous') return <LoginPage />;
  if (status === 'restoring')
    return <SplashScreen error={restoreError} onRetry={restoreSession} />;

  return <RouterProvider router={router} />;
}
