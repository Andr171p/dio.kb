import clsx from 'clsx';
import {
  ChevronRight,
  FilePlus,
  FileText,
  Folder,
  FolderInput,
  FolderOpen,
  FolderPlus,
  FolderX,
  MoreHorizontal,
  Pencil,
  Plus,
  Shield,
  Trash2,
} from 'lucide-react';
import { useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router';
import { hasPermission } from '@entities/access-grant';
import {
  loadNavigation,
  useSpaceNavigation,
  type NavigationNode,
} from '@entities/collection';
import { isAdmin, useCurrentUser } from '@entities/session';
import { SpaceIcon, type Space } from '@entities/space';
import {
  archiveCollection,
  removePlacement,
} from '@features/manage-collection';
import { routes } from '@shared/config/routes';
import { confirmAction } from '@shared/ui/dialog';
import { Menu, MenuItem, MenuSeparator } from '@shared/ui/menu';
import { usePopover } from '@shared/ui/popover';
import { Skeleton } from '@shared/ui/skeleton';
import { toast } from '@shared/ui/toast';
import {
  openSidebarDialog,
  toggleExpanded,
  useSidebar,
} from '../model/sidebar-store';
import styles from './NavigationTree.module.scss';

const INDENT = 14;

interface NodeContext {
  space: Space;
  canWrite: boolean;
  admin: boolean;
}

function NodeMenu({
  node,
  context,
}: {
  node: NavigationNode;
  context: NodeContext;
}) {
  const { triggerProps, popoverProps } = usePopover();
  const navigate = useNavigate();
  const { space, canWrite, admin } = context;
  const isCollection = node.type === 'collection';

  if (!canWrite && !admin) return null;

  const archive = () =>
    confirmAction({
      title: `Архивировать «${node.title}»?`,
      description:
        'Архивировать можно только пустую коллекцию: сначала перенесите или уберите её элементы.',
      confirmLabel: 'Архивировать',
      tone: 'danger',
      onConfirm: async () => {
        await archiveCollection(space.id, node.id);
        toast.success('Коллекция архивирована');
      },
    });

  const removeFromCollection = async () => {
    if (!node.placementId) return;
    await removePlacement(space.id, node.placementId).catch(() => null);
  };

  return (
    <>
      <button
        type="button"
        className={styles.action}
        aria-label={`Действия: ${node.title}`}
        {...triggerProps}
      >
        <MoreHorizontal size={15} aria-hidden />
      </button>
      <Menu {...popoverProps} placement="bottom-start">
        {canWrite && isCollection && (
          <>
            <MenuItem
              icon={FilePlus}
              onSelect={() =>
                void navigate(routes.newArticle(space.id, node.id))
              }
            >
              Новая статья
            </MenuItem>
            <MenuItem
              icon={FolderPlus}
              onSelect={() =>
                openSidebarDialog({
                  kind: 'create-collection',
                  spaceId: space.id,
                  parent: { id: node.id, title: node.title },
                })
              }
            >
              Вложенная коллекция
            </MenuItem>
            <MenuItem
              icon={Pencil}
              onSelect={() =>
                openSidebarDialog({
                  kind: 'rename-collection',
                  spaceId: space.id,
                  node,
                })
              }
            >
              Переименовать
            </MenuItem>
          </>
        )}
        {canWrite && (
          <>
            {!isCollection && (
              <MenuItem
                icon={FolderPlus}
                onSelect={() =>
                  openSidebarDialog({
                    kind: 'placement',
                    spaceId: space.id,
                    node,
                    mode: 'add',
                  })
                }
              >
                Добавить в коллекцию
              </MenuItem>
            )}
            <MenuItem
              icon={FolderInput}
              onSelect={() =>
                openSidebarDialog({
                  kind: 'placement',
                  spaceId: space.id,
                  node,
                  // Корневую коллекцию «перемещаем», создавая ей размещение
                  mode: node.placementId || isCollection ? 'move' : 'add',
                })
              }
            >
              Переместить
            </MenuItem>
            {!isCollection && node.placementId && (
              <MenuItem
                icon={FolderX}
                onSelect={() => void removeFromCollection()}
              >
                Убрать из коллекции
              </MenuItem>
            )}
          </>
        )}
        {admin && (
          <MenuItem
            icon={Shield}
            onSelect={() =>
              openSidebarDialog({
                kind: 'access',
                resource: { type: node.type, id: node.id },
                title: node.title,
                spaceId: space.id,
              })
            }
          >
            Доступ
          </MenuItem>
        )}
        {canWrite && isCollection && (
          <>
            <MenuSeparator />
            <MenuItem icon={Trash2} tone="danger" onSelect={archive}>
              Архивировать
            </MenuItem>
          </>
        )}
      </Menu>
    </>
  );
}

function TreeNode({
  node,
  depth,
  context,
}: {
  node: NavigationNode;
  depth: number;
  context: NodeContext;
}) {
  const { articleId } = useParams();
  const expanded = useSidebar((state) => Boolean(state.expanded[node.id]));
  const isCollection = node.type === 'collection';
  const active = !isCollection && node.id === articleId;
  const style = { paddingLeft: 8 + depth * INDENT };

  const label = isCollection ? (
    <button
      type="button"
      className={styles.label}
      aria-expanded={expanded}
      onClick={() => toggleExpanded(node.id)}
    >
      <ChevronRight
        size={14}
        className={clsx(styles.chevron, expanded && styles.chevronOpen)}
        aria-hidden
      />
      {expanded ? (
        <FolderOpen size={15} className={styles.icon} aria-hidden />
      ) : (
        <Folder size={15} className={styles.icon} aria-hidden />
      )}
      <span className={styles.title}>{node.title}</span>
    </button>
  ) : (
    <Link
      to={routes.article(node.id)}
      className={styles.label}
      aria-current={active ? 'page' : undefined}
    >
      <span className={styles.chevronSpacer} />
      <FileText size={15} className={styles.icon} aria-hidden />
      <span
        className={clsx(styles.title, node.status === 'draft' && styles.draft)}
      >
        {node.title}
      </span>
      {node.status === 'draft' && (
        <span
          className={styles.draftDot}
          title="Черновик"
          aria-label="Черновик"
        />
      )}
    </Link>
  );

  return (
    <li role="treeitem" aria-expanded={isCollection ? expanded : undefined}>
      <div className={clsx(styles.row, active && styles.active)} style={style}>
        {label}
        <div className={styles.actions}>
          {isCollection && context.canWrite && (
            <Link
              to={routes.newArticle(context.space.id, node.id)}
              className={styles.action}
              aria-label={`Новая статья в «${node.title}»`}
              title="Новая статья"
            >
              <Plus size={15} aria-hidden />
            </Link>
          )}
          <NodeMenu node={node} context={context} />
        </div>
      </div>
      {isCollection && expanded && (
        <ul role="group" className={styles.group}>
          {node.children.map((child) => (
            <TreeNode
              key={child.placementId ?? child.id}
              node={child}
              depth={depth + 1}
              context={context}
            />
          ))}
          {node.children.length === 0 && (
            <li
              className={styles.emptyRow}
              style={{ paddingLeft: 8 + (depth + 1) * INDENT + 20 }}
            >
              Пусто
            </li>
          )}
        </ul>
      )}
    </li>
  );
}

function SpaceMenu({ space, context }: { space: Space; context: NodeContext }) {
  const { triggerProps, popoverProps } = usePopover();
  const navigate = useNavigate();

  if (!context.canWrite && !context.admin) return null;

  return (
    <>
      <button
        type="button"
        className={styles.action}
        aria-label={`Действия: ${space.name}`}
        {...triggerProps}
      >
        <MoreHorizontal size={15} aria-hidden />
      </button>
      <Menu {...popoverProps} placement="bottom-start">
        {context.canWrite && (
          <>
            <MenuItem
              icon={FilePlus}
              onSelect={() => void navigate(routes.newArticle(space.id))}
            >
              Новая статья
            </MenuItem>
            <MenuItem
              icon={FolderPlus}
              onSelect={() =>
                openSidebarDialog({
                  kind: 'create-collection',
                  spaceId: space.id,
                  parent: null,
                })
              }
            >
              Новая коллекция
            </MenuItem>
          </>
        )}
        {context.admin && (
          <MenuItem
            icon={Shield}
            onSelect={() =>
              openSidebarDialog({
                kind: 'access',
                resource: { type: 'space', id: space.id },
                title: space.name,
              })
            }
          >
            Доступ
          </MenuItem>
        )}
      </Menu>
    </>
  );
}

/** Пространство с деревом коллекций и статей. Дерево загружается при раскрытии. */
export function SpaceTree({ space }: { space: Space }) {
  const { spaceId } = useParams();
  const user = useCurrentUser();
  const expanded = useSidebar((state) => Boolean(state.expanded[space.id]));
  const navigation = useSpaceNavigation(space.id);

  const context: NodeContext = {
    space,
    canWrite: hasPermission(space.permissions, 'WRITE'),
    admin: isAdmin(user),
  };

  useEffect(() => {
    if (expanded) void loadNavigation(space.id);
  }, [expanded, space.id]);

  const data = navigation?.data;
  const empty =
    data && data.collections.length === 0 && data.unplacedArticles.length === 0;

  return (
    <li role="treeitem" aria-expanded={expanded}>
      <div
        className={clsx(
          styles.row,
          styles.spaceRow,
          spaceId === space.id && styles.activeSpace,
        )}
      >
        <button
          type="button"
          className={styles.spaceToggle}
          aria-label={expanded ? 'Свернуть' : 'Развернуть'}
          onClick={() => toggleExpanded(space.id)}
        >
          <ChevronRight
            size={14}
            className={clsx(styles.chevron, expanded && styles.chevronOpen)}
            aria-hidden
          />
        </button>
        <Link to={routes.space(space.id)} className={styles.label}>
          <SpaceIcon spaceKey={space.key} />
          <span className={styles.title}>{space.name}</span>
        </Link>
        <div className={styles.actions}>
          {context.canWrite && (
            <Link
              to={routes.newArticle(space.id)}
              className={styles.action}
              aria-label={`Новая статья в «${space.name}»`}
              title="Новая статья"
            >
              <Plus size={15} aria-hidden />
            </Link>
          )}
          <SpaceMenu space={space} context={context} />
        </div>
      </div>

      {expanded && (
        <ul role="group" className={styles.group}>
          {navigation?.status === 'loading' && !data && (
            <li className={styles.skeletons}>
              <Skeleton height={12} width="70%" />
              <Skeleton height={12} width="55%" />
            </li>
          )}
          {navigation?.status === 'error' && !data && (
            <li className={styles.emptyRow} style={{ paddingLeft: 30 }}>
              Не удалось загрузить
            </li>
          )}
          {data?.collections.map((node) => (
            <TreeNode key={node.id} node={node} depth={1} context={context} />
          ))}
          {data?.unplacedArticles.map((node) => (
            <TreeNode key={node.id} node={node} depth={1} context={context} />
          ))}
          {empty && (
            <li className={styles.emptyRow} style={{ paddingLeft: 30 }}>
              Пока нет статей
            </li>
          )}
        </ul>
      )}
    </li>
  );
}
