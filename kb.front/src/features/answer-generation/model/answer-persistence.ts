const STORAGE_KEY = 'dios.kb.answer-run';

interface AnswerPointer {
  answerId: string;
  question: string;
}

/** Сохраняет указатель на AnswerRun — чтобы не потерять ответ при уходе со страницы. */
export function persistAnswerPointer(answerId: string, question: string) {
  try {
    const payload: AnswerPointer = { answerId, question };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // private mode / quota
  }
}

export function readAnswerPointer(): AnswerPointer | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<AnswerPointer>;
    if (
      typeof parsed.answerId !== 'string' ||
      typeof parsed.question !== 'string'
    )
      return null;
    return { answerId: parsed.answerId, question: parsed.question };
  } catch {
    return null;
  }
}

export function clearAnswerPointer() {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}
