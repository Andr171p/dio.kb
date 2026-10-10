import { ImageOff } from 'lucide-react';
import { useEffect, useState, type ComponentProps } from 'react';
import { mediaIdFromSrc, resolveMediaUrl } from '@shared/api';
import styles from './MediaImage.module.scss';

/**
 * Изображение статьи. `media://<id>` — стабильная ссылка на Media Service:
 * временный URL запрашиваем при показе и никогда не сохраняем в Markdown.
 */
export function MediaImage({ src, alt, ...props }: ComponentProps<'img'>) {
  const mediaId = mediaIdFromSrc(typeof src === 'string' ? src : null);
  const [resolved, setResolved] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!mediaId) return;
    let cancelled = false;
    resolveMediaUrl(mediaId)
      .then((url) => !cancelled && setResolved(url))
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [mediaId]);

  if (failed)
    return (
      <span className={styles.imageError} role="img" aria-label={alt}>
        <ImageOff size={18} aria-hidden />
        Не удалось загрузить изображение{alt ? `: ${alt}` : ''}
      </span>
    );

  const url = mediaId ? resolved : src;
  if (!url)
    return <span className={styles.imagePlaceholder} aria-label={alt} />;

  return (
    <img
      src={url}
      alt={alt ?? ''}
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
      {...props}
    />
  );
}
