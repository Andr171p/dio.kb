import { AppHeader } from '@widgets/app-shell';
import { routes } from '@shared/config/routes';
import { ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import styles from './NotFoundPage.module.scss';

export function NotFoundPage() {
  return (
    <>
      <AppHeader crumbs={[{ label: 'Страница не найдена' }]} />
      <div className={styles.page}>
        <EmptyState
          title="Страница не найдена"
          description="Возможно, ссылка устарела или у вас нет доступа к этому материалу."
          action={<ButtonLink to={routes.home()}>На главную</ButtonLink>}
        />
      </div>
    </>
  );
}
