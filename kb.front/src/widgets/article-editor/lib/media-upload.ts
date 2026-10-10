import { Extension, type Editor } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';

export interface MediaUploadOptions {
  /** Загружает файл и возвращает ссылку `media://<id>` */
  upload: (file: File) => Promise<string>;
  onError: (error: unknown) => void;
}

const isImage = (file: File) => file.type.startsWith('image/');

/**
 * Вставляет изображение сразу (blob-превью со спиннером) и подменяет его ссылкой
 * `media://<id>`, когда загрузка в Media Service завершится.
 */
export function insertImages(
  editor: Editor,
  files: File[],
  options: MediaUploadOptions,
  position?: number,
) {
  files.filter(isImage).forEach((file) => {
    const uploadId = crypto.randomUUID();
    const previewUrl = URL.createObjectURL(file);
    const content = {
      type: 'image',
      attrs: {
        src: previewUrl,
        alt: file.name.replace(/\.[^.]+$/, ''),
        uploadId,
      },
    };

    const chain = editor.chain().focus();
    if (position === undefined) chain.insertContent(content);
    else chain.insertContentAt(position, content);
    chain.run();

    const replace = (src: string | null) => {
      const { state } = editor;
      state.doc.descendants((node, pos) => {
        if (node.type.name !== 'image' || node.attrs.uploadId !== uploadId)
          return true;
        const tr =
          src === null
            ? state.tr.delete(pos, pos + node.nodeSize)
            : state.tr.setNodeMarkup(pos, undefined, {
                ...node.attrs,
                src,
                uploadId: null,
              });
        editor.view.dispatch(tr.setMeta('addToHistory', false));
        return false;
      });
      URL.revokeObjectURL(previewUrl);
    };

    options
      .upload(file)
      .then((src) => replace(src))
      .catch((error: unknown) => {
        replace(null);
        options.onError(error);
      });
  });
}

/** Вставка и перетаскивание изображений в редактор. */
export const MediaUpload = Extension.create<MediaUploadOptions>({
  name: 'mediaUpload',

  addOptions() {
    return {
      upload: () => Promise.reject(new Error('upload is not configured')),
      onError: () => undefined,
    };
  },

  addProseMirrorPlugins() {
    const { editor, options } = this;

    return [
      new Plugin({
        key: new PluginKey('mediaUpload'),
        props: {
          handlePaste: (_view, event) => {
            const files = [...(event.clipboardData?.files ?? [])].filter(
              isImage,
            );
            if (files.length === 0) return false;
            insertImages(editor, files, options);
            return true;
          },
          handleDrop: (view, event) => {
            const files = [...(event.dataTransfer?.files ?? [])].filter(
              isImage,
            );
            if (files.length === 0) return false;
            const position = view.posAtCoords({
              left: event.clientX,
              top: event.clientY,
            })?.pos;
            insertImages(editor, files, options, position);
            return true;
          },
        },
      }),
    ];
  },
});
