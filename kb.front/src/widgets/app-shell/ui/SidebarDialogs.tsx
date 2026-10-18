import { CreateCollectionDialog } from '@features/create-collection';
import { CreateSpaceDialog } from '@features/create-space';
import {
  PlacementDialog,
  RenameCollectionDialog,
} from '@features/manage-collection';
import { closeSidebarDialog, useSidebar } from '../model/sidebar-store';

/** Диалоги действий из навигации. Открыт не больше одного. */
export function SidebarDialogs() {
  const dialog = useSidebar((state) => state.dialog);
  if (!dialog) return null;

  const props = { open: true, onClose: closeSidebarDialog };

  switch (dialog.kind) {
    case 'create-space':
      return <CreateSpaceDialog {...props} />;
    case 'create-collection':
      return (
        <CreateCollectionDialog
          {...props}
          spaceId={dialog.spaceId}
          parent={dialog.parent}
        />
      );
    case 'rename-collection':
      return (
        <RenameCollectionDialog
          {...props}
          spaceId={dialog.spaceId}
          collection={{ id: dialog.node.id, title: dialog.node.title }}
        />
      );
    case 'placement':
      return (
        <PlacementDialog
          {...props}
          spaceId={dialog.spaceId}
          node={dialog.node}
          mode={dialog.mode}
        />
      );
  }
}
