/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AUTH_API_URL?: string;
  readonly VITE_KB_API_URL?: string;
  readonly VITE_MEDIA_STORAGE_URL?: string;
  readonly VITE_DIOS_URL?: string;
  /** Через запятую, например `http://localhost:3000,https://desk.dios.ru` */
  readonly VITE_TRUSTED_ORIGINS?: string;
  readonly VITE_HELP_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
