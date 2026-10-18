import { createBrowserRouter, Navigate } from 'react-router';
import { routes } from '@shared/config/routes';
import { AppLayout, type RouteHandle } from './ui/AppLayout';
import { RouteError } from './ui/RouteError';
import { SplashScreen } from './ui/SplashScreen';

const accessPage = () =>
  import('@pages/access').then(({ AccessPage }) => ({ Component: AccessPage }));

/** Страницы грузятся по требованию: редактор и подсветка кода не нужны на главной. */
export const router = createBrowserRouter([
  {
    path: '/',
    Component: AppLayout,
    ErrorBoundary: RouteError,
    // Пока грузится чанк страницы при первом открытии
    HydrateFallback: SplashScreen,
    children: [
      {
        index: true,
        lazy: () =>
          import('@pages/home').then(({ HomePage }) => ({
            Component: HomePage,
          })),
      },
      {
        path: 'search',
        lazy: () =>
          import('@pages/search').then(({ SearchPage }) => ({
            Component: SearchPage,
          })),
      },
      {
        path: 'recent',
        lazy: () =>
          import('@pages/recent').then(({ RecentPage }) => ({
            Component: RecentPage,
          })),
      },
      {
        path: 'spaces/:spaceId',
        lazy: () =>
          import('@pages/space').then(({ SpacePage }) => ({
            Component: SpacePage,
          })),
      },
      { path: 'spaces/:spaceId/access', lazy: accessPage },
      {
        path: 'spaces/:spaceId/collections/:collectionId/access',
        lazy: accessPage,
      },
      {
        path: 'spaces/:spaceId/new',
        lazy: () =>
          import('@pages/article-editor').then(({ NewArticlePage }) => ({
            Component: NewArticlePage,
          })),
      },
      {
        path: 'articles/:articleId',
        lazy: () =>
          import('@pages/article').then(({ ArticlePage }) => ({
            Component: ArticlePage,
          })),
      },
      {
        path: 'articles/:articleId/focus',
        handle: { bare: true } satisfies RouteHandle,
        lazy: () =>
          import('@pages/article').then(({ ArticleFocusPage }) => ({
            Component: ArticleFocusPage,
          })),
      },
      {
        path: 'articles/:articleId/edit',
        lazy: () =>
          import('@pages/article-editor').then(({ EditArticlePage }) => ({
            Component: EditArticlePage,
          })),
      },
      {
        path: 'articles/:articleId/history',
        lazy: () =>
          import('@pages/article-history').then(({ ArticleHistoryPage }) => ({
            Component: ArticleHistoryPage,
          })),
      },
      { path: 'articles/:articleId/access', lazy: accessPage },
      { path: 'login', element: <Navigate to={routes.home()} replace /> },
      {
        path: '*',
        lazy: () =>
          import('@pages/not-found').then(({ NotFoundPage }) => ({
            Component: NotFoundPage,
          })),
      },
    ],
  },
]);
