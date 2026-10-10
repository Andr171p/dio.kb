import oneC from 'highlight.js/lib/languages/1c';
import apache from 'highlight.js/lib/languages/apache';
import dockerfile from 'highlight.js/lib/languages/dockerfile';
import nginx from 'highlight.js/lib/languages/nginx';
import powershell from 'highlight.js/lib/languages/powershell';
import { common } from 'lowlight';

/** Языки подсветки: одни и те же в просмотре статьи и в редакторе. */
export const codeLanguages = {
  ...common,
  '1c': oneC,
  apache,
  dockerfile,
  nginx,
  powershell,
};

/** Языки для выбора в блоке кода редактора: [id, подпись]. */
export const CODE_LANGUAGE_OPTIONS: [string, string][] = [
  ['plaintext', 'Текст'],
  ['bash', 'Bash'],
  ['powershell', 'PowerShell'],
  ['1c', '1С'],
  ['sql', 'SQL'],
  ['python', 'Python'],
  ['javascript', 'JavaScript'],
  ['typescript', 'TypeScript'],
  ['json', 'JSON'],
  ['yaml', 'YAML'],
  ['xml', 'XML / HTML'],
  ['css', 'CSS'],
  ['java', 'Java'],
  ['kotlin', 'Kotlin'],
  ['csharp', 'C#'],
  ['go', 'Go'],
  ['rust', 'Rust'],
  ['php', 'PHP'],
  ['ruby', 'Ruby'],
  ['cpp', 'C++'],
  ['c', 'C'],
  ['ini', 'INI / TOML'],
  ['dockerfile', 'Dockerfile'],
  ['nginx', 'nginx'],
  ['apache', 'Apache'],
  ['diff', 'Diff'],
  ['markdown', 'Markdown'],
  ['graphql', 'GraphQL'],
];

export function codeLanguageLabel(language: string | null | undefined): string {
  return (
    CODE_LANGUAGE_OPTIONS.find(([id]) => id === language)?.[1] ??
    language ??
    'Текст'
  );
}
