import {
  NodeViewContent,
  NodeViewWrapper,
  type ReactNodeViewProps,
} from '@tiptap/react';
import { Check, Copy } from 'lucide-react';
import { CODE_LANGUAGE_OPTIONS } from '@shared/lib/code-languages';
import { useCopyToClipboard } from '@shared/lib/hooks';
import styles from './CodeBlockView.module.scss';

/** Блок кода в редакторе: выбор языка подсветки и копирование. */
export function CodeBlockView({
  node,
  updateAttributes,
  editor,
}: ReactNodeViewProps) {
  const { copied, copy } = useCopyToClipboard();
  const language = (node.attrs.language as string | null) ?? 'plaintext';
  const known = CODE_LANGUAGE_OPTIONS.some(([id]) => id === language);

  return (
    <NodeViewWrapper className={styles.block}>
      <div className={styles.header} contentEditable={false}>
        <select
          className={styles.language}
          value={language}
          aria-label="Язык подсветки"
          disabled={!editor.isEditable}
          onChange={(event) =>
            updateAttributes({
              language:
                event.target.value === 'plaintext' ? null : event.target.value,
            })
          }
        >
          {!known && <option value={language}>{language}</option>}
          {CODE_LANGUAGE_OPTIONS.map(([id, label]) => (
            <option key={id} value={id}>
              {label}
            </option>
          ))}
        </select>
        <button
          type="button"
          className={styles.copy}
          onClick={() => void copy(node.textContent)}
        >
          {copied ? (
            <Check size={13} aria-hidden />
          ) : (
            <Copy size={13} aria-hidden />
          )}
          {copied ? 'Скопировано' : 'Копировать'}
        </button>
      </div>
      <pre spellCheck={false}>
        <NodeViewContent<'code'> as="code" />
      </pre>
    </NodeViewWrapper>
  );
}
