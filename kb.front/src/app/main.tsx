import '@fontsource-variable/inter';
import '@fontsource-variable/jetbrains-mono';
import './styles/index.scss';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { initSession } from '@entities/session';
import { syncThemeWithDocument } from '@shared/lib/theme';
import { App } from './App';

syncThemeWithDocument();
initSession();

const root = document.getElementById('root');
if (!root) throw new Error('Не найден контейнер #root');

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
