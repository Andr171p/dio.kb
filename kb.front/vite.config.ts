/// <reference types="vitest/config" />
import { fileURLToPath, URL } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv, type Plugin, type ProxyOptions } from 'vite';

const LAYERS = ['app', 'pages', 'widgets', 'features', 'entities', 'shared'];

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [
      react(),
      contentSecurityPolicy([
        env.VITE_AUTH_API_URL,
        env.VITE_KB_API_URL,
        env.VITE_MEDIA_STORAGE_URL,
      ]),
    ],
    resolve: {
      alias: Object.fromEntries(
        LAYERS.map((layer) => [
          `@${layer}`,
          fileURLToPath(new URL(`./src/${layer}`, import.meta.url)),
        ]),
      ),
    },
    server: {
      // Node резолвит localhost в ::1, и Vite слушает только IPv6 —
      // браузеры, которые идут на 127.0.0.1, получают отказ в соединении
      host: '127.0.0.1',
      port: 5174,
      proxy: {
        '/auth-api': proxyTo(
          env.AUTH_API_TARGET || 'http://localhost:8001',
          '/auth-api',
        ),
        '/kb-api': proxyTo(
          env.KB_API_TARGET || 'http://localhost:8010',
          '/kb-api',
        ),
      },
    },
    preview: { host: '127.0.0.1', port: 5174 },
    test: {
      environment: 'jsdom',
      include: ['src/**/*.test.{ts,tsx}'],
      css: false,
    },
  };
});

function proxyTo(target: string, prefix: string): ProxyOptions {
  return {
    target,
    changeOrigin: true,
    rewrite: (path) => path.slice(prefix.length),
  };
}

/**
 * CSP для production-сборки. В dev не подключается: HMR Vite использует inline-скрипты.
 * Абсолютные адреса API и хранилища медиа попадают в connect-src, относительные покрывает 'self'.
 */
function contentSecurityPolicy(apiUrls: (string | undefined)[]): Plugin {
  const apiOrigins = apiUrls
    .filter((url): url is string => Boolean(url && /^https?:\/\//.test(url)))
    .map((url) => new URL(url).origin);

  const policy = [
    "default-src 'self'",
    "script-src 'self'",
    // ProseMirror и подсветка кода пишут inline-стили в разметку
    "style-src 'self' 'unsafe-inline'",
    // Превью ссылок и вложения Media Service (presigned URL) — с внешних адресов
    "img-src 'self' data: blob: https: http:",
    "font-src 'self' data:",
    ['connect-src', "'self'", ...apiOrigins].join(' '),
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ');

  return {
    name: 'content-security-policy',
    apply: 'build',
    transformIndexHtml: () => [
      {
        tag: 'meta',
        attrs: { 'http-equiv': 'Content-Security-Policy', content: policy },
        injectTo: 'head-prepend',
      },
    ],
  };
}
