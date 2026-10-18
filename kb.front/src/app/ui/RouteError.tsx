import { RotateCcw } from 'lucide-react';
import { useRouteError } from 'react-router';
import { Button } from '@shared/ui/button';
import { LogoMark } from '@shared/ui/logo';
import styles from './SplashScreen.module.scss';

/** Непредвиденная ошибка рендера или загрузки чанка (например, после деплоя новой версии). */
export function RouteError() {
  const error = useRouteError();
  console.error(error);

  return (
    <div className={styles.splash}>
      <LogoMark size={44} />
      <p className={styles.error}>
        Что-то пошло не так. Обновите страницу — если ошибка повторится,
        сообщите администратору.
      </p>
      <Button icon={RotateCcw} onClick={() => window.location.reload()}>
        Обновить
      </Button>
    </div>
  );
}
