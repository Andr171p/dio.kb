import { Extension, type Editor, type Range } from '@tiptap/core';
import { PluginKey } from '@tiptap/pm/state';
import { ReactRenderer } from '@tiptap/react';
import Suggestion, {
  type SuggestionKeyDownProps,
  type SuggestionProps,
} from '@tiptap/suggestion';
import type { LucideIcon } from 'lucide-react';
import { SlashMenu, type SlashMenuHandle } from '../ui/SlashMenu';

export interface SlashItem {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  /** Слова для поиска: «h2», «таблица», «code» */
  keywords: string[];
  run: (editor: Editor, range: Range) => void;
}

export interface SlashCommandsOptions {
  items: () => SlashItem[];
}

function matches(item: SlashItem, query: string): boolean {
  const needle = query.toLocaleLowerCase('ru');
  return [item.title, ...item.keywords].some((word) =>
    word.toLocaleLowerCase('ru').includes(needle),
  );
}

/** Меню блоков по «/»: заголовки, списки, таблица, код, изображение. */
export const SlashCommands = Extension.create<SlashCommandsOptions>({
  name: 'slashCommands',

  addOptions() {
    return { items: () => [] };
  },

  addProseMirrorPlugins() {
    return [
      Suggestion<SlashItem, SlashItem>({
        editor: this.editor,
        pluginKey: new PluginKey('slashCommands'),
        char: '/',
        items: ({ query }) =>
          this.options.items().filter((item) => matches(item, query)),
        command: ({ editor, range, props }) => props.run(editor, range),
        // Не в блоке кода: там «/» — обычный символ
        allow: ({ state, range }) =>
          state.doc.resolve(range.from).parent.type.name !== 'codeBlock',
        render: () => {
          let renderer: ReactRenderer<SlashMenuHandle> | null = null;
          let unmount: (() => void) | null = null;

          return {
            onStart: (props: SuggestionProps<SlashItem, SlashItem>) => {
              renderer = new ReactRenderer(SlashMenu, {
                props,
                editor: props.editor,
              });
              unmount = props.mount(renderer.element);
            },
            onUpdate: (props: SuggestionProps<SlashItem, SlashItem>) => {
              renderer?.updateProps(props);
            },
            onKeyDown: ({ event }: SuggestionKeyDownProps) => {
              if (event.key === 'Escape') return false;
              return renderer?.ref?.onKeyDown(event) ?? false;
            },
            onExit: () => {
              unmount?.();
              renderer?.destroy();
              renderer = null;
            },
          };
        },
      }),
    ];
  },
});
