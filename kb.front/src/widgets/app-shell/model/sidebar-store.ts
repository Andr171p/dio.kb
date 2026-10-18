import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { NavigationNode } from '@entities/collection';
import { registerStoreReset } from '@shared/lib/store-reset';

export type SidebarDialog =
  | { kind: 'create-space' }
  | {
      kind: 'create-collection';
      spaceId: string;
      parent: { id: string; title: string } | null;
    }
  | { kind: 'rename-collection'; spaceId: string; node: NavigationNode }
  | {
      kind: 'placement';
      spaceId: string;
      node: NavigationNode;
      mode: 'add' | 'move';
    };

interface SidebarState {
  /** Открыт как выезжающая панель на мобильных */
  mobileOpen: boolean;
  /** Раскрытые пространства и коллекции */
  expanded: Record<string, boolean>;
  dialog: SidebarDialog | null;
}

export const useSidebar = create<SidebarState>()(
  persist(
    (): SidebarState => ({
      mobileOpen: false,
      expanded: {},
      dialog: null,
    }),
    {
      name: 'dios.kb.sidebar',
      partialize: ({ expanded }) => ({ expanded }),
    },
  ),
);

registerStoreReset(() =>
  useSidebar.setState({ expanded: {}, dialog: null, mobileOpen: false }),
);

export function toggleExpanded(id: string) {
  useSidebar.setState(({ expanded }) => ({
    expanded: { ...expanded, [id]: !expanded[id] },
  }));
}

/** Раскрывает путь до элемента: пространство и коллекции-предки. */
export function revealInSidebar(ids: string[]) {
  useSidebar.setState(({ expanded }) => ({
    expanded: {
      ...expanded,
      ...Object.fromEntries(ids.map((id) => [id, true])),
    },
  }));
}

export function setMobileSidebarOpen(mobileOpen: boolean) {
  useSidebar.setState({ mobileOpen });
}

export function openSidebarDialog(dialog: SidebarDialog) {
  useSidebar.setState({ dialog });
}

export function closeSidebarDialog() {
  useSidebar.setState({ dialog: null });
}
