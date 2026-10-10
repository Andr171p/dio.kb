import { ApiError } from './api-error';
import { diosApi } from './clients';

/** Каноническая ссылка на вложение Media Service в Markdown: `media://<id>`. */
export const MEDIA_SCHEME = 'media://';

interface PresignedUpload {
  upload_url: string;
  storage_key: string;
}

interface PresignedDownload {
  download_url: string;
  expires_in: number;
}

interface Attachment {
  id: string;
  original_filename: string;
  mime_type: string;
}

/**
 * Владелец файла в Media Service. Тип «статья базы знаний» Media Service пока не поддерживает,
 * поэтому файлы принадлежат загрузившему пользователю (см. kb.back/docs/architecture/decisions.md).
 */
interface MediaOwner {
  type: 'user';
  id: string;
}

export function mediaIdFromSrc(src: string | null | undefined): string | null {
  return src?.startsWith(MEDIA_SCHEME) ? src.slice(MEDIA_SCHEME.length) : null;
}

/** Загружает файл в хранилище по presigned URL и возвращает ссылку `media://<id>`. */
export async function uploadMedia(
  file: File,
  owner: MediaOwner,
  signal?: AbortSignal,
): Promise<string> {
  const contentType = file.type || 'application/octet-stream';
  const meta = {
    content_type: contentType,
    owner_type: owner.type,
    owner_id: owner.id,
  };

  const upload = await diosApi.post<PresignedUpload>(
    '/api/v1/attachments/presigned-upload',
    { body: { filename: file.name, ...meta }, signal },
  );

  const response = await fetch(upload.upload_url, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': contentType },
    signal,
  });
  if (!response.ok)
    throw new ApiError(response.status, 'Не удалось загрузить файл');

  const attachment = await diosApi.post<Attachment>(
    '/api/v1/attachments/confirm-upload',
    {
      body: {
        storage_key: upload.storage_key,
        original_filename: file.name,
        ...meta,
      },
      signal,
    },
  );
  return `${MEDIA_SCHEME}${attachment.id}`;
}

/** Обновляем ссылку заранее, чтобы она не истекла, пока картинка грузится */
const EXPIRY_MARGIN_MS = 60_000;
const downloadUrls = new Map<
  string,
  Promise<{ url: string; expiresAt: number }>
>();

/** Временная ссылка на скачивание вложения; кешируется до истечения срока. */
export async function resolveMediaUrl(mediaId: string): Promise<string> {
  const cached = downloadUrls.get(mediaId);
  if (cached) {
    const entry = await cached.catch(() => null);
    if (entry && entry.expiresAt - EXPIRY_MARGIN_MS > Date.now())
      return entry.url;
  }

  const request = diosApi
    .get<PresignedDownload>(
      `/api/v1/attachments/${encodeURIComponent(mediaId)}/presigned-download`,
    )
    .then(({ download_url, expires_in }) => ({
      url: download_url,
      expiresAt: Date.now() + expires_in * 1000,
    }));

  downloadUrls.set(mediaId, request);
  request.catch(() => downloadUrls.delete(mediaId));
  return (await request).url;
}

export function clearMediaCache() {
  downloadUrls.clear();
}
