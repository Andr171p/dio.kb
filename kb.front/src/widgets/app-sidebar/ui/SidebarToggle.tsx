import { PanelLeftOpen } from 'lucide-react';
import { useMediaQuery } from '@shared/lib/hooks';
import { IconButton } from '@shared/ui/button';
import {
  setMobileSidebarOpen,
  toggleSidebar,
  useSidebar,
} from '../model/sidebar-store';

/** Кнопка открытия навигации: на мобильных и когда панель скрыта на десктопе. */
export function SidebarToggle() {
  const collapsed = useSidebar((state) => state.collapsed);
  const mobile = useMediaQuery('(max-width: 900px)');

  if (!mobile && !collapsed) return null;

  return (
    <IconButton
      icon={PanelLeftOpen}
      label="Показать навигацию"
      onClick={() => (mobile ? setMobileSidebarOpen(true) : toggleSidebar())}
    />
  );
}
