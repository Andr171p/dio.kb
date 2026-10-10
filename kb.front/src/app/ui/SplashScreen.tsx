import { Button } from '@shared/ui/button';
import { LogoMark } from '@shared/ui/logo';
import { Spinner } from '@shared/ui/spinner';
import styles from './SplashScreen.module.scss';

interface SplashScreenProps {
  error?: string | null;
  onRetry?: () => void;
}

export function SplashScreen({ error, onRetry }: SplashScreenProps) {
  return (
    <div className={styles.splash}>
      <LogoMark size={36} />
      {error ? (
        <>
          <p className={styles.error}>{error}</p>
          {onRetry && <Button onClick={onRetry}>Повторить</Button>}
        </>
      ) : (
        <Spinner size={20} label="Загрузка" />
      )}
    </div>
  );
}
