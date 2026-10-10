import clsx from 'clsx';
import { Folder, FolderRoot } from 'lucide-react';
import { useMemo, useState } from 'react';
import {
  flattenCollections,
  useSpaceNavigation,
  type NavigationNode,
} from '@entities/collection';
import { Button } from '@shared/ui/button';
import { Dialog, DialogActions } from '@shared/ui/dialog';
import { toast } from '@shared/ui/toast';
import {
  addToCollection,
  movePlacement,
  removePlacement,
} from '../model/collection-actions';
import styles from './ManageCollection.module.scss';

const ROOT = 'root';

interface PlacementDialogProps {
  open: boolean;
  onClose: () => void;
  spaceId: string;
  node: NavigationNode;
  /**
   * add — ещё одно размещение статьи (статья может быть в нескольких коллекциях);
   * move — перенос текущего размещения
   */
  mode: 'add' | 'move';
}

function descendantIds(node: NavigationNode): Set<string> {
  const ids = new Set<string>([node.id]);
  const walk = (nodes: NavigationNode[]) =>
    nodes.forEach((child) => {
      ids.add(child.id);
      walk(child.children);
    });
  walk(node.children);
  return ids;
}

/** Выбор коллекции для размещения или переноса элемента навигации. */
export function PlacementDialog({
  open,
  onClose,
  spaceId,
  node,
  mode,
}: PlacementDialogProps) {
  const navigation = useSpaceNavigation(spaceId)?.data;
  const [selected, setSelected] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const options = useMemo(() => {
    if (!navigation) return [];
    // Коллекцию нельзя вложить в саму себя или в своих потомков
    const excluded =
      node.type === 'collection' ? descendantIds(node) : new Set<string>();
    return flattenCollections(navigation.collections).filter(
      ({ node: option }) => !excluded.has(option.id),
    );
  }, [navigation, node]);

  // В корень: коллекция становится корневой, статья — «вне коллекций»
  const canMoveToRoot = mode === 'move' && node.placementId !== null;

  const submit = async () => {
    if (!selected) return;
    setPending(true);
    try {
      if (selected === ROOT && node.placementId) {
        await removePlacement(spaceId, node.placementId);
      } else if (mode === 'move' && node.placementId) {
        await movePlacement(spaceId, node.placementId, {
          collectionId: selected,
        });
      } else {
        await addToCollection(spaceId, selected, {
          type: node.type,
          id: node.id,
        });
      }
      toast.success(mode === 'add' ? 'Добавлено в коллекцию' : 'Перемещено');
      onClose();
    } catch {
      // Ошибку уже показал тост
    } finally {
      setPending(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      size="md"
      title={
        mode === 'add' ? 'Добавить в коллекцию' : `Переместить «${node.title}»`
      }
      description={
        mode === 'add'
          ? 'Статья может находиться в нескольких коллекциях одновременно.'
          : undefined
      }
    >
      <div className={styles.options} role="listbox" aria-label="Коллекции">
        {canMoveToRoot && (
          <button
            type="button"
            role="option"
            aria-selected={selected === ROOT}
            className={clsx(
              styles.option,
              selected === ROOT && styles.selected,
            )}
            onClick={() => setSelected(ROOT)}
          >
            <FolderRoot size={15} aria-hidden />
            {node.type === 'collection'
              ? 'В корень пространства'
              : 'Вне коллекций'}
          </button>
        )}
        {options.map(({ node: option, depth }) => (
          <button
            key={option.id}
            type="button"
            role="option"
            aria-selected={selected === option.id}
            className={clsx(
              styles.option,
              selected === option.id && styles.selected,
            )}
            style={{ paddingLeft: 12 + depth * 18 }}
            onClick={() => setSelected(option.id)}
          >
            <Folder size={15} aria-hidden />
            <span className={styles.optionLabel}>{option.title}</span>
          </button>
        ))}
        {options.length === 0 && !canMoveToRoot && (
          <p className={styles.empty}>
            В пространстве нет подходящих коллекций.
          </p>
        )}
      </div>
      <DialogActions>
        <Button onClick={onClose}>Отмена</Button>
        <Button
          variant="primary"
          disabled={!selected}
          loading={pending}
          onClick={() => void submit()}
        >
          {mode === 'add' ? 'Добавить' : 'Переместить'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
