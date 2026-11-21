import { create } from 'zustand';
import { describeError, isAbortError } from '@shared/api';
import { registerStoreReset } from '@shared/lib/store-reset';
import {
  dismissKnowledgeGap,
  getKnowledgeGap,
  listKnowledgeGaps,
  patchKnowledgeGap,
  reopenKnowledgeGap,
  resolveKnowledgeGap,
  startKnowledgeGap,
} from './api';
import type { GapKind, KnowledgeGap } from './types';

interface GapsState {
  status: 'idle' | 'loading' | 'ready' | 'error';
  items: KnowledgeGap[];
  error: string | null;
  selected: KnowledgeGap | null;
  selectedError: string | null;
  selectedLoading: boolean;
}

export const useKnowledgeGaps = create<GapsState>()(() => ({
  status: 'idle',
  items: [],
  error: null,
  selected: null,
  selectedError: null,
  selectedLoading: false,
}));

registerStoreReset(() =>
  useKnowledgeGaps.setState(useKnowledgeGaps.getInitialState(), true),
);

let listController: AbortController | null = null;
let detailController: AbortController | null = null;

export async function loadKnowledgeGaps(): Promise<void> {
  listController?.abort();
  const controller = new AbortController();
  listController = controller;
  useKnowledgeGaps.setState({ status: 'loading', error: null });
  try {
    const { items } = await listKnowledgeGaps({
      signal: controller.signal,
      limit: 100,
    });
    useKnowledgeGaps.setState({ status: 'ready', items, error: null });
  } catch (error) {
    if (isAbortError(error)) return;
    useKnowledgeGaps.setState({
      status: 'error',
      error: describeError(error),
    });
  }
}

export function clearSelectedKnowledgeGap() {
  detailController?.abort();
  detailController = null;
  useKnowledgeGaps.setState({
    selected: null,
    selectedError: null,
    selectedLoading: false,
  });
}

export async function loadKnowledgeGap(gapId: string): Promise<void> {
  detailController?.abort();
  const controller = new AbortController();
  detailController = controller;
  useKnowledgeGaps.setState({
    selectedLoading: true,
    selectedError: null,
  });
  try {
    const selected = await getKnowledgeGap(gapId, controller.signal);
    useKnowledgeGaps.setState({
      selected,
      selectedLoading: false,
      selectedError: null,
    });
  } catch (error) {
    if (isAbortError(error)) return;
    useKnowledgeGaps.setState({
      selected: null,
      selectedLoading: false,
      selectedError: describeError(error),
    });
  }
}

function upsert(gap: KnowledgeGap) {
  useKnowledgeGaps.setState(({ items, selected }) => ({
    items: items.map((item) => (item.id === gap.id ? gap : item)),
    selected: selected?.id === gap.id ? gap : selected,
  }));
}

export async function classifyKnowledgeGap(gapId: string, kind: GapKind) {
  upsert(await patchKnowledgeGap(gapId, { kind }));
}

export async function assignKnowledgeGapOwner(
  gapId: string,
  ownerId: string | null,
) {
  upsert(await patchKnowledgeGap(gapId, { ownerId }));
}

export async function takeKnowledgeGap(gapId: string) {
  upsert(await startKnowledgeGap(gapId));
}

export async function completeKnowledgeGap(gapId: string, note: string) {
  upsert(await resolveKnowledgeGap(gapId, note));
}

export async function rejectKnowledgeGap(gapId: string, reason: string) {
  upsert(await dismissKnowledgeGap(gapId, reason));
}

export async function reopenSelectedKnowledgeGap(gapId: string) {
  upsert(await reopenKnowledgeGap(gapId));
}
