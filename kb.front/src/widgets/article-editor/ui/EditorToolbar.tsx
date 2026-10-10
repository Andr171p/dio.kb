import { NodeSelection } from '@tiptap/pm/state';
import { useEditorState, type Editor } from '@tiptap/react';
import { BubbleMenu } from '@tiptap/react/menus';
import clsx from 'clsx';
import {
  ArrowDownToLine,
  ArrowLeftToLine,
  ArrowRightToLine,
  ArrowUpToLine,
  Bold,
  Code,
  Columns3,
  Heading2,
  Heading3,
  Italic,
  Link2,
  Quote,
  Rows3,
  Strikethrough,
  TableProperties,
  Trash2,
  type LucideIcon,
} from 'lucide-react';
import { useState } from 'react';
import { LinkEditor } from './LinkEditor';
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

/** Плавающая панель форматирования выделенного текста. */
export function SelectionToolbar({ editor }: { editor: Editor }) {
  const [editingLink, setEditingLink] = useState(false);

  const state = useEditorState({
    editor,
    selector: ({ editor: current }) => ({
      bold: current.isActive('bold'),
      italic: current.isActive('italic'),
      strike: current.isActive('strike'),
      code: current.isActive('code'),
      link: current.isActive('link'),
      h2: current.isActive('heading', { level: 2 }),
      h3: current.isActive('heading', { level: 3 }),
      quote: current.isActive('blockquote'),
    }),
  });

  const chain = () => editor.chain().focus();

  return (
    <BubbleMenu
      editor={editor}
      pluginKey="selectionToolbar"
      className={styles.toolbar}
      options={{ placement: 'top', offset: 8 }}
      shouldShow={({ editor: current, state: editorState, from, to }) => {
        if (!current.isEditable || from === to) return false;
        // Изображения и блоки кода не форматируются инлайн-разметкой
        if (editorState.selection instanceof NodeSelection) return false;
        return !current.isActive('codeBlock');
      }}
    >
      {editingLink ? (
        <LinkEditor editor={editor} onDone={() => setEditingLink(false)} />
      ) : (
        <div className={styles.group}>
          <Tool
            icon={Bold}
            label="Жирный"
            active={state.bold}
            onClick={() => chain().toggleBold().run()}
          />
          <Tool
            icon={Italic}
            label="Курсив"
            active={state.italic}
            onClick={() => chain().toggleItalic().run()}
          />
          <Tool
            icon={Strikethrough}
            label="Зачёркнутый"
            active={state.strike}
            onClick={() => chain().toggleStrike().run()}
          />
          <Tool
            icon={Code}
            label="Код"
            active={state.code}
            onClick={() => chain().toggleCode().run()}
          />
          <Tool
            icon={Link2}
            label="Ссылка"
            active={state.link}
            onClick={() => setEditingLink(true)}
          />
          <Separator />
          <Tool
            icon={Heading2}
            label="Заголовок 2"
            active={state.h2}
            onClick={() => chain().toggleHeading({ level: 2 }).run()}
          />
          <Tool
            icon={Heading3}
            label="Заголовок 3"
            active={state.h3}
            onClick={() => chain().toggleHeading({ level: 3 }).run()}
          />
          <Tool
            icon={Quote}
            label="Цитата"
            active={state.quote}
            onClick={() => chain().toggleBlockquote().run()}
          />
        </div>
      )}
    </BubbleMenu>
  );
}

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
