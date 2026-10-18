import { useEditorState, type Editor } from '@tiptap/react';
import clsx from 'clsx';
import {
  Bold,
  ChevronDown,
  Code,
  Heading2,
  Italic,
  Link2,
  List,
  ListChecks,
  ListOrdered,
  SquareCode,
  Strikethrough,
  type LucideIcon,
} from 'lucide-react';
import { useState } from 'react';
import { Menu, MenuItem } from '@shared/ui/menu';
import { usePopover } from '@shared/ui/popover';
import { LinkEditor } from './LinkEditor';
import styles from './EditorToolbar.module.scss';

interface ToolProps {
  icon: LucideIcon;
  label: string;
  active?: boolean;
  onClick: () => void;
}

function Tool({ icon: Icon, label, active, onClick }: ToolProps) {
  return (
    <button
      type="button"
      className={clsx(styles.tool, active && styles.active)}
      aria-label={label}
      aria-pressed={active}
      title={label}
      // Не уводим фокус из редактора, иначе пропадёт выделение
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
    >
      <Icon size={17} aria-hidden />
    </button>
  );
}

const Separator = () => <span className={styles.separator} aria-hidden />;

type BlockType = 'paragraph' | 'h2' | 'h3' | 'h4' | 'quote' | 'code';

const BLOCK_LABELS: Record<BlockType, string> = {
  paragraph: 'Текст',
  h2: 'Заголовок 2',
  h3: 'Заголовок 3',
  h4: 'Заголовок 4',
  quote: 'Цитата',
  code: 'Код',
};

function BlockTypeMenu({
  editor,
  current,
}: {
  editor: Editor;
  current: BlockType;
}) {
  const { triggerProps, popoverProps } = usePopover();
  const chain = () => editor.chain().focus();

  const apply: Record<BlockType, () => void> = {
    paragraph: () => chain().setParagraph().run(),
    h2: () => chain().setHeading({ level: 2 }).run(),
    h3: () => chain().setHeading({ level: 3 }).run(),
    h4: () => chain().setHeading({ level: 4 }).run(),
    quote: () => chain().setParagraph().toggleBlockquote().run(),
    code: () => chain().setCodeBlock().run(),
  };

  return (
    <>
      <button
        type="button"
        className={styles.blockType}
        onMouseDown={(event) => event.preventDefault()}
        {...triggerProps}
      >
        {BLOCK_LABELS[current]}
        <ChevronDown size={14} aria-hidden />
      </button>
      <Menu {...popoverProps} placement="bottom-start">
        {(Object.keys(BLOCK_LABELS) as BlockType[]).map((type) => (
          <MenuItem
            key={type}
            selected={type === current}
            onMouseDown={(event) => event.preventDefault()}
            onSelect={apply[type]}
          >
            {BLOCK_LABELS[type]}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}

/**
 * Панель форматирования над текстом: закреплена под шапкой при прокрутке.
 * Плавающая панель — поэтому деликатное стекло.
 */
export function FormatToolbar({ editor }: { editor: Editor }) {
  const [editingLink, setEditingLink] = useState(false);

  const state = useEditorState({
    editor,
    selector: ({ editor: current }) => {
      const block: BlockType = current.isActive('codeBlock')
        ? 'code'
        : current.isActive('blockquote')
          ? 'quote'
          : current.isActive('heading', { level: 2 })
            ? 'h2'
            : current.isActive('heading', { level: 3 })
              ? 'h3'
              : current.isActive('heading', { level: 4 })
                ? 'h4'
                : 'paragraph';
      return {
        block,
        bold: current.isActive('bold'),
        italic: current.isActive('italic'),
        strike: current.isActive('strike'),
        code: current.isActive('code'),
        link: current.isActive('link'),
        bullet: current.isActive('bulletList'),
        ordered: current.isActive('orderedList'),
        task: current.isActive('taskList'),
        codeBlock: current.isActive('codeBlock'),
      };
    },
  });

  const chain = () => editor.chain().focus();

  return (
    <div
      className={styles.formatToolbar}
      role="toolbar"
      aria-label="Форматирование"
    >
      {editingLink ? (
        <LinkEditor editor={editor} onDone={() => setEditingLink(false)} />
      ) : (
        <div className={styles.group}>
          <BlockTypeMenu editor={editor} current={state.block} />
          <Separator />
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
          <Separator />
          <Tool
            icon={Heading2}
            label="Заголовок раздела"
            active={state.block === 'h2'}
            onClick={() => chain().toggleHeading({ level: 2 }).run()}
          />
          <Tool
            icon={List}
            label="Маркированный список"
            active={state.bullet}
            onClick={() => chain().toggleBulletList().run()}
          />
          <Tool
            icon={ListOrdered}
            label="Нумерованный список"
            active={state.ordered}
            onClick={() => chain().toggleOrderedList().run()}
          />
          <Tool
            icon={ListChecks}
            label="Чеклист"
            active={state.task}
            onClick={() => chain().toggleTaskList().run()}
          />
          <Tool
            icon={Link2}
            label="Ссылка"
            active={state.link}
            onClick={() => setEditingLink(true)}
          />
          <Tool
            icon={Code}
            label="Код в строке"
            active={state.code}
            onClick={() => chain().toggleCode().run()}
          />
          <Tool
            icon={SquareCode}
            label="Блок кода"
            active={state.codeBlock}
            onClick={() => chain().toggleCodeBlock().run()}
          />
        </div>
      )}
    </div>
  );
}
