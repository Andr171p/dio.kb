import { FileQuestion } from 'lucide-react';
import { SidebarToggle } from '@widgets/app-sidebar';
import { routes } from '@shared/config/routes';
import { ButtonLink } from '@shared/ui/button';
import { EmptyState } from '@shared/ui/empty-state';
import { Topbar } from '@shared/ui/topbar';

export function NotFoundPage() {
  return (
    <>
      <Topbar start={<SidebarToggle />} />
      <EmptyState
        icon={FileQuestion}
        title="Страница не найдена"
        description="Возможно, ссылка устарела или у вас нет доступа к этому материалу."
        action={
          <ButtonLink to={routes.home()} variant="primary">
            На главную
          </ButtonLink>
        }
      />
    </>
  );
}
