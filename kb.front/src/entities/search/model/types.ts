export interface SearchFragment {
  chunkId: string;
  /** Markdown-фрагмент опубликованной редакции */
  text: string;
  headingPath: string[];
  /** Якорь раздела для прямой ссылки */
  anchor: string | null;
}

export interface SearchResult {
  article: {
    id: string;
    spaceId: string;
    slug: string;
    title: string;
    revisionId: string;
    publishedAt: string;
  };
  fragments: SearchFragment[];
}

export interface SearchQuery {
  query: string;
  spaceIds?: string[];
  limit?: number;
}
