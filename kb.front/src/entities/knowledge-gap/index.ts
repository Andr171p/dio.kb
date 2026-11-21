export {
  dismissKnowledgeGap,
  getKnowledgeGap,
  listKnowledgeGaps,
  patchKnowledgeGap,
  reopenKnowledgeGap,
  resolveKnowledgeGap,
  startKnowledgeGap,
} from './model/api';
export {
  assignKnowledgeGapOwner,
  classifyKnowledgeGap,
  clearSelectedKnowledgeGap,
  completeKnowledgeGap,
  loadKnowledgeGap,
  loadKnowledgeGaps,
  rejectKnowledgeGap,
  reopenSelectedKnowledgeGap,
  takeKnowledgeGap,
  useKnowledgeGaps,
} from './model/gaps-store';
export {
  GAP_KIND_ACTION,
  GAP_KIND_LABELS,
  GAP_STATUS_LABELS,
  type GapKind,
  type GapStatus,
  type KnowledgeGap,
} from './model/types';
