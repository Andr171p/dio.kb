import clsx from 'clsx';
import type { Element, ElementContent } from 'hast';
import { Check, Copy, Link2 } from 'lucide-react';
import { memo, useRef, type ComponentProps, type ReactNode } from 'react';
import Markdown, { defaultUrlTransform, type Components } from 'react-markdown';
import { Link } from 'react-router';
import rehypeHighlight from 'rehype-highlight';
import rehypeSlug from 'rehype-slug';
import remarkGfm from 'remark-gfm';
import { LinkCard, LinkHoverPreview } from '@entities/link-preview';
import { MEDIA_SCHEME } from '@shared/api';
import { articleIdFromHref, routes } from '@shared/config/routes';
import { codeLanguageLabel, codeLanguages } from '@shared/lib/code-languages';
import { useCopyToClipboard } from '@shared/lib/hooks';
import { MediaImage } from '@shared/ui/media-image';
import { toast } from '@shared/ui/toast';
import styles from './ArticleContent.module.scss';

/** Разрешаем `media://` для вложений; остальное — стандартная санитизация (без javascript: и т.п.). */
function urlTransform(url: string): string {
  return url.startsWith(MEDIA_SCHEME) ? url : defaultUrlTransform(url);
}

function textOf(node: ElementContent): string {
  if (node.type === 'text') return node.value;
  if (node.type === 'element') return node.children.map(textOf).join('');
  return '';
}

/** Абзац из одной «голой» ссылки показываем карточкой; в Markdown он остаётся обычной ссылкой. */
function standaloneLink(node: Element | undefined): string | null {
  if (!node) return null;
  const meaningful = node.children.filter(
    (child) => !(child.type === 'text' && !child.value.trim()),
  );
  const [only] = meaningful;
  if (
    meaningful.length !== 1 ||
    only.type !== 'element' ||
    only.tagName !== 'a'
  )
    return null;

  const href = String(only.properties.href ?? '');
  return href && textOf(only).trim() === href ? href : null;
}

function isAppLink(href: string): boolean {
  return href.startsWith('/') && !href.startsWith('//');
}

/** Ссылка приложения (`/articles/...`) или полный адрес этого же приложения → путь для роутера. */
function appPath(href: string): string | null {
  if (isAppLink(href)) return href;
  try {
    const url = new URL(href);
    return url.origin === window.location.origin
      ? url.pathname + url.search + url.hash
      : null;
  } catch {
    return null;
  }
}

function ArticleLink({ href = '', children, ...props }: ComponentProps<'a'>) {
  if (href.startsWith('#'))
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );

  const path = appPath(href);
  if (path) {
    const articleId = articleIdFromHref(path);
    const link = <Link to={path}>{children}</Link>;
    return articleId ? (
      <LinkHoverPreview href={routes.article(articleId)}>
        {link}
      </LinkHoverPreview>
    ) : (
      link
    );
  }

  const link = (
    <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
      {children}
    </a>
  );
  return /^https?:\/\//.test(href) ? (
    <LinkHoverPreview href={href}>{link}</LinkHoverPreview>
  ) : (
    link
  );
}

function CodeBlock({
  children,
  node,
}: ComponentProps<'pre'> & { node?: Element }) {
  const ref = useRef<HTMLPreElement>(null);
  const { copied, copy } = useCopyToClipboard();
  const code = node?.children.find(
    (child): child is Element =>
      child.type === 'element' && child.tagName === 'code',
  );
  const className = code?.properties.className;
  const language = (Array.isArray(className) ? className : [])
    .map(String)
    .find((name) => name.startsWith('language-'))
    ?.slice('language-'.length);

  return (
    <div className={styles.codeBlock}>
      <div className={styles.codeHeader}>
        <span className={styles.codeLanguage}>
          {codeLanguageLabel(language)}
        </span>
        <button
          type="button"
          className={styles.codeCopy}
          onClick={() => {
            const text = ref.current?.innerText ?? '';
            copy(text).catch(() => toast.error('Не удалось скопировать'));
          }}
        >
          {copied ? (
            <Check size={13} aria-hidden />
          ) : (
            <Copy size={13} aria-hidden />
          )}
          {copied ? 'Скопировано' : 'Копировать'}
        </button>
      </div>
      <pre ref={ref}>{children}</pre>
    </div>
  );
}

function Heading({
  level,
  id,
  children,
}: {
  level: 1 | 2 | 3 | 4 | 5 | 6;
  id?: string;
  children?: ReactNode;
}) {
  const Tag = `h${level}` as const;
  const { copy } = useCopyToClipboard();

  return (
    <Tag id={id} className={styles.heading}>
      {children}
      {id && (
        <a
          href={`#${id}`}
          className={styles.anchor}
          aria-label="Ссылка на раздел"
          onClick={() => {
            const url = `${window.location.origin}${window.location.pathname}#${id}`;
            copy(url)
              .then(() => toast.success('Ссылка на раздел скопирована'))
              .catch(() => undefined);
          }}
        >
          <Link2 size={15} aria-hidden />
        </a>
      )}
    </Tag>
  );
}

const components: Components = {
  a: ({ node: _node, ...props }) => <ArticleLink {...props} />,
  p: ({ node, children, ...props }) => {
    const href = standaloneLink(node);
    if (href) {
      const path = appPath(href);
      const articleId = path && articleIdFromHref(path);
      return (
        <div className={styles.linkCard}>
          {path ? (
            <LinkCard href={articleId ? routes.article(articleId) : path} />
          ) : (
            <LinkCard href={href} target="_blank" rel="noopener noreferrer" />
          )}
        </div>
      );
    }
    return <p {...props}>{children}</p>;
  },
  img: ({ src, alt, title }) => (
    <MediaImage
      src={typeof src === 'string' ? src : undefined}
      alt={alt}
      title={title}
    />
  ),
  pre: ({ node, children }) => <CodeBlock node={node}>{children}</CodeBlock>,
  table: ({ node: _node, ...props }) => (
    <div className={styles.tableWrap}>
      <table {...props} />
    </div>
  ),
  h1: ({ id, children }) => (
    <Heading level={1} id={id}>
      {children}
    </Heading>
  ),
  h2: ({ id, children }) => (
    <Heading level={2} id={id}>
      {children}
    </Heading>
  ),
  h3: ({ id, children }) => (
    <Heading level={3} id={id}>
      {children}
    </Heading>
  ),
  h4: ({ id, children }) => (
    <Heading level={4} id={id}>
      {children}
    </Heading>
  ),
  h5: ({ id, children }) => (
    <Heading level={5} id={id}>
      {children}
    </Heading>
  ),
  h6: ({ id, children }) => (
    <Heading level={6} id={id}>
      {children}
    </Heading>
  ),
};

interface ArticleContentProps {
  markdown: string;
  className?: string;
}

/**
 * Безопасный рендер Markdown статьи: HTML из текста не исполняется, ссылки санитизируются,
 * якоря заголовков совпадают с якорями поиска (GitHub-style slug).
 */
export const ArticleContent = memo(function ArticleContent({
  markdown,
  className,
}: ArticleContentProps) {
  return (
    <div className={clsx(styles.content, className)}>
      <Markdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[
          rehypeSlug,
          [rehypeHighlight, { detect: false, languages: codeLanguages }],
        ]}
        components={components}
        urlTransform={urlTransform}
      >
        {markdown}
      </Markdown>
    </div>
  );
});
