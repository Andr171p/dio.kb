const time = new Intl.DateTimeFormat('ru-RU', {
  hour: '2-digit',
  minute: '2-digit',
});
const day = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'short',
});
const dayWithYear = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});
const full = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});
const relative = new Intl.RelativeTimeFormat('ru-RU', { numeric: 'auto' });

/** «14:05» для сегодняшних дат, «27 сент.» для этого года, иначе с годом. */
export function formatShortDate(
  value: string | Date,
  now = new Date(),
): string {
  const date = new Date(value);

  if (date.toDateString() === now.toDateString()) return time.format(date);
  if (date.getFullYear() === now.getFullYear()) return day.format(date);
  return dayWithYear.format(date);
}

/** «11 октября 2026 г., 14:05» — для подсказок и истории. */
export function formatDateTime(value: string | Date): string {
  return full.format(new Date(value));
}

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/** «только что», «5 минут назад», «вчера»; старше недели — короткая дата. */
export function formatRelative(value: string | Date, now = new Date()): string {
  const diff = new Date(value).getTime() - now.getTime();
  const abs = Math.abs(diff);

  if (abs < MINUTE) return 'только что';
  if (abs < HOUR) return relative.format(Math.round(diff / MINUTE), 'minute');
  if (abs < DAY) return relative.format(Math.round(diff / HOUR), 'hour');
  if (abs < 7 * DAY) return relative.format(Math.round(diff / DAY), 'day');
  return formatShortDate(value, now);
}
