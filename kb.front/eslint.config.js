import js from '@eslint/js';
import prettier from 'eslint-config-prettier';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import { defineConfig, globalIgnores } from 'eslint/config';
import globals from 'globals';
import tseslint from 'typescript-eslint';

/** Слои FSD сверху вниз: слой может импортировать только те, что ниже него. */
const LAYERS = ['app', 'pages', 'widgets', 'features', 'entities', 'shared'];
const SLICED_LAYERS = ['pages', 'widgets', 'features', 'entities'];

const layerBoundaries = LAYERS.map((layer, index) => {
  const upperLayers = LAYERS.slice(0, index);
  const patterns = [
    {
      regex: `^@(${SLICED_LAYERS.join('|')})/[^/]+/`,
      message: 'Импортируйте слайс только через его public API (index.ts).',
    },
  ];

  if (upperLayers.length > 0) {
    patterns.push({
      regex: `^@(${upperLayers.join('|')})(/|$)`,
      message: `Слой «${layer}» не может зависеть от вышележащих слоёв (${upperLayers.join(', ')}).`,
    });
  }

  if (SLICED_LAYERS.includes(layer)) {
    patterns.push({
      regex: `^@${layer}(/|$)`,
      message:
        'Слайсы одного слоя не зависят друг от друга. Внутри слайса используйте относительные импорты.',
      // Сущности могут ссылаться на типы друг друга (аналог @x-нотации FSD)
      allowTypeImports: layer === 'entities',
    });
  }

  return {
    files: [`src/${layer}/**/*.{ts,tsx}`],
    rules: {
      '@typescript-eslint/no-restricted-imports': ['error', { patterns }],
    },
  };
});

export default defineConfig([
  globalIgnores(['dist', 'node_modules']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommendedTypeChecked,
      reactHooks.configs.flat['recommended-latest'],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2023,
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { ignoreRestSiblings: true },
      ],
      '@typescript-eslint/no-misused-promises': [
        'error',
        { checksVoidReturn: { attributes: false } },
      ],
      'no-console': ['warn', { allow: ['warn', 'error'] }],
    },
  },
  ...layerBoundaries,
  prettier,
]);
