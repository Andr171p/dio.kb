import type { Editor } from '@tiptap/react';
import { BubbleMenu } from '@tiptap/react/menus';
import clsx from 'clsx';
import {
  ArrowDownToLine,
  ArrowLeftToLine,
  ArrowRightToLine,
  ArrowUpToLine,
  Columns3,
  Rows3,
  TableProperties,
  Trash2,
  type LucideIcon,
} from 'lucide-react';
import styles from './EditorToolbar.module.scss';

interface ToolProps {
  icon: LucideIcon;
  label: string;
  active?: boolean;
  danger?: boolean;
  onClick: () => void;
}

function Tool({ icon: Icon, label, active, danger, onClick }: ToolProps) {
  return (
    <button
      type="button"
      className={clsx(
        styles.tool,
        active && styles.active,
        danger && styles.danger,
      )}
      aria-label={label}
      aria-pressed={active}
      title={label}
      // Не уводим фокус из редактора, иначе пропадёт выделение
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
    >
      <Icon size={15} aria-hidden />
    </button>
  );
}

const Separator = () => <span className={styles.separator} aria-hidden />;

/** Панель таблицы: появляется, когда курсор в ячейке. */
export function TableToolbar({ editor }: { editor: Editor }) {
  const chain = () => editor.chain().focus();

  return (
    <BubbleMenu
      editor={editor}
      pluginKey="tableToolbar"
      className={styles.toolbar}
      options={{ placement: 'top-start', offset: 10 }}
      shouldShow={({ editor: current, from, to }) =>
        current.isEditable && from === to && current.isActive('table')
      }
      getReferencedVirtualElement={() => {
        // Привязываем панель к таблице целиком, а не к курсору
        const { view, state } = editor;
        const { $from } = state.selection;
        for (let depth = $from.depth; depth > 0; depth -= 1) {
          if ($from.node(depth).type.name === 'table') {
            const dom = view.nodeDOM($from.before(depth));
            const element = dom instanceof HTMLElement ? dom : null;
            if (element)
              return {
                getBoundingClientRect: () => element.getBoundingClientRect(),
              };
          }
        }
        return null;
      }}
    >
      <div className={styles.group}>
        <Tool
          icon={ArrowUpToLine}
          label="Строка выше"
          onClick={() => chain().addRowBefore().run()}
        />
        <Tool
          icon={ArrowDownToLine}
          label="Строка ниже"
          onClick={() => chain().addRowAfter().run()}
        />
        <Tool
          icon={Rows3}
          label="Удалить строку"
          danger
          onClick={() => chain().deleteRow().run()}
        />
        <Separator />
        <Tool
          icon={ArrowLeftToLine}
          label="Столбец слева"
          onClick={() => chain().addColumnBefore().run()}
        />
        <Tool
          icon={ArrowRightToLine}
          label="Столбец справа"
          onClick={() => chain().addColumnAfter().run()}
        />
        <Tool
          icon={Columns3}
          label="Удалить столбец"
          danger
          onClick={() => chain().deleteColumn().run()}
        />
        <Separator />
        <Tool
          icon={TableProperties}
          label="Строка заголовков"
          onClick={() => chain().toggleHeaderRow().run()}
        />
        <Tool
          icon={Trash2}
          label="Удалить таблицу"
          danger
          onClick={() => chain().deleteTable().run()}
        />
      </div>
    </BubbleMenu>
  );
}
