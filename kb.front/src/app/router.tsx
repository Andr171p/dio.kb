import { createBrowserRouter, Navigate } from 'react-router';
import { routes } from '@shared/config/routes';
import { AppLayout } from './ui/AppLayout';
import { RouteError } from './ui/RouteError';
import { SplashScreen } from './ui/SplashScreen';

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
        path: 'spaces/:spaceId',
        lazy: () =>
          import('@pages/space').then(({ SpacePage }) => ({
            Component: SpacePage,
          })),
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
