import type { AnyExtension, Editor, Range } from '@tiptap/core';
import { CodeBlockLowlight } from '@tiptap/extension-code-block-lowlight';
import Image from '@tiptap/extension-image';
import { TaskItem, TaskList } from '@tiptap/extension-list';
import { TableKit } from '@tiptap/extension-table';
import { CharacterCount, Placeholder } from '@tiptap/extensions';
import { Markdown } from '@tiptap/markdown';
import { ReactNodeViewRenderer } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { createLowlight } from 'lowlight';
import {
  CheckSquare,
  Code2,
  Heading1,
  Heading2,
  Heading3,
  ImagePlus,
  List,
  ListOrdered,
  Minus,
  Pilcrow,
  Quote,
  Table,
} from 'lucide-react';
import { codeLanguages } from '@shared/lib/code-languages';
import { CodeBlockView } from '../ui/CodeBlockView';
import { ImageView } from '../ui/ImageView';
import { MediaUpload, type MediaUploadOptions } from './media-upload';
import { SlashCommands, type SlashItem } from './slash-commands';

const lowlight = createLowlight(codeLanguages);

/** Изображение — блочный узел; `uploadId` живёт только в редакторе и в Markdown не попадает. */
const MediaImageNode = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      uploadId: {
        default: null,
        renderHTML: () => ({}),
        parseHTML: () => null,
      },
    };
  },
  addNodeView() {
    return ReactNodeViewRenderer(ImageView);
  },
}).configure({ inline: false, allowBase64: false });

const CodeBlock = CodeBlockLowlight.extend({
  addNodeView() {
    return ReactNodeViewRenderer(CodeBlockView);
  },
}).configure({ lowlight, enableTabIndentation: true });

interface ExtensionsOptions extends MediaUploadOptions {
  /** Выбор файла изображения через системный диалог */
  pickImage: (insert: (files: File[]) => void) => void;
  insertImages: (files: File[]) => void;
}

function slashItems({
  pickImage,
  insertImages,
}: ExtensionsOptions): SlashItem[] {
  const block =
    (apply: (editor: Editor) => void) => (editor: Editor, range: Range) => {
      editor.chain().focus().deleteRange(range).run();
      apply(editor);
    };

  return [
    {
      id: 'paragraph',
      title: 'Текст',
      description: 'Обычный абзац',
      icon: Pilcrow,
      keywords: ['text', 'paragraph', 'абзац'],
      run: block((editor) => editor.chain().focus().setParagraph().run()),
    },
    {
      id: 'h1',
      title: 'Заголовок 1',
      description: 'Крупный раздел',
      icon: Heading1,
      keywords: ['h1', 'heading', 'заголовок'],
      run: block((editor) =>
        editor.chain().focus().setHeading({ level: 1 }).run(),
      ),
    },
    {
      id: 'h2',
      title: 'Заголовок 2',
      description: 'Раздел — попадёт в оглавление',
      icon: Heading2,
      keywords: ['h2', 'heading', 'заголовок', 'раздел'],
      run: block((editor) =>
        editor.chain().focus().setHeading({ level: 2 }).run(),
      ),
    },
    {
      id: 'h3',
      title: 'Заголовок 3',
      description: 'Подраздел',
      icon: Heading3,
      keywords: ['h3', 'heading', 'заголовок', 'подраздел'],
      run: block((editor) =>
        editor.chain().focus().setHeading({ level: 3 }).run(),
      ),
    },
    {
      id: 'bullet',
      title: 'Маркированный список',
      description: 'Пункты без порядка',
      icon: List,
      keywords: ['list', 'ul', 'bullet', 'список'],
      run: block((editor) => editor.chain().focus().toggleBulletList().run()),
    },
    {
      id: 'ordered',
      title: 'Нумерованный список',
      description: 'Последовательность шагов',
      icon: ListOrdered,
      keywords: ['ol', 'numbered', 'список', 'шаги'],
      run: block((editor) => editor.chain().focus().toggleOrderedList().run()),
    },
    {
      id: 'tasks',
      title: 'Чеклист',
      description: 'Список с отметками',
      icon: CheckSquare,
      keywords: ['todo', 'task', 'checklist', 'задачи', 'чеклист'],
      run: block((editor) => editor.chain().focus().toggleTaskList().run()),
    },
    {
      id: 'table',
      title: 'Таблица',
      description: '3 × 3 с заголовком',
      icon: Table,
      keywords: ['table', 'таблица', 'grid'],
      run: block((editor) =>
        editor
          .chain()
          .focus()
          .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
          .run(),
      ),
    },
    {
      id: 'code',
      title: 'Блок кода',
      description: 'С подсветкой синтаксиса',
      icon: Code2,
      keywords: ['code', 'код', 'snippet', 'bash', 'sql'],
      run: block((editor) => editor.chain().focus().toggleCodeBlock().run()),
    },
    {
      id: 'quote',
      title: 'Цитата',
      description: 'Выделенный фрагмент или примечание',
      icon: Quote,
      keywords: ['quote', 'blockquote', 'цитата', 'примечание'],
      run: block((editor) => editor.chain().focus().toggleBlockquote().run()),
    },
    {
      id: 'image',
      title: 'Изображение',
      description: 'Загрузить файл в Media Service',
      icon: ImagePlus,
      keywords: ['image', 'img', 'picture', 'картинка', 'скриншот'],
      run: block(() => pickImage(insertImages)),
    },
    {
      id: 'divider',
      title: 'Разделитель',
      description: 'Горизонтальная линия',
      icon: Minus,
      keywords: ['hr', 'divider', 'line', 'линия'],
      run: block((editor) => editor.chain().focus().setHorizontalRule().run()),
    },
  ];
}

export function createExtensions(options: ExtensionsOptions): AnyExtension[] {
  const items = slashItems(options);

  return [
    StarterKit.configure({
      // В Markdown нет подчёркивания — не даём создать то, что не сохранится
      underline: false,
      codeBlock: false,
      heading: { levels: [1, 2, 3, 4] },
      link: {
        openOnClick: false,
        autolink: true,
        defaultProtocol: 'https',
        HTMLAttributes: { rel: 'noopener noreferrer', target: null },
      },
    }),
    Markdown,
    TableKit.configure({ table: { resizable: false } }),
    TaskList,
    TaskItem.configure({ nested: true }),
    CodeBlock,
    MediaImageNode,
    MediaUpload.configure({ upload: options.upload, onError: options.onError }),
    SlashCommands.configure({ items: () => items }),
    CharacterCount,
    Placeholder.configure({
      placeholder: ({ node }) => {
        if (node.type.name === 'heading')
          return `Заголовок ${node.attrs.level as number}`;
        return 'Введите текст или «/» для выбора блока';
      },
    }),
  ];
}
