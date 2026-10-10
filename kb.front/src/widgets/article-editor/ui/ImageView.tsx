import { NodeViewWrapper, type ReactNodeViewProps } from '@tiptap/react';
import clsx from 'clsx';
import { MediaImage } from '@shared/ui/media-image';
import { Spinner } from '@shared/ui/spinner';
import styles from './ImageView.module.scss';

/** Изображение в редакторе: `media://` разрешается через Media Service, пока грузится — спиннер. */
export function ImageView({ node, selected }: ReactNodeViewProps) {
  const { src, alt, title, uploadId } = node.attrs as {
    src: string;
    alt: string | null;
    title: string | null;
    uploadId: string | null;
  };

  return (
    <NodeViewWrapper
      className={clsx(styles.image, selected && styles.selected)}
      data-drag-handle
    >
      <MediaImage
        src={src}
        alt={alt ?? undefined}
        title={title ?? undefined}
        draggable={false}
      />
      {uploadId && (
        <span className={styles.uploading}>
          <Spinner size={18} label="Загрузка изображения" />
        </span>
      )}
    </NodeViewWrapper>
  );
}
