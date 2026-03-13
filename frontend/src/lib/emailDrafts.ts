/** Local drafts storage - each draft has metadata for organization */

export interface EmailDraft {
  id: string;
  description: string;
  targetAudience: string;
  company: string;
  subject: string;
  body: string;
  recipientName: string;
  recipientEmail: string;
  recipientTitle: string;
  createdAt: string;
}

const STORAGE_KEY = 'yucg_email_drafts';

export function loadDrafts(): EmailDraft[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveDraft(draft: Omit<EmailDraft, 'id' | 'createdAt'>): EmailDraft {
  const drafts = loadDrafts();
  const newDraft: EmailDraft = {
    ...draft,
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
  };
  drafts.unshift(newDraft);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(drafts));
  return newDraft;
}

export function updateDraft(id: string, updates: Partial<EmailDraft>): void {
  const drafts = loadDrafts();
  const idx = drafts.findIndex((d) => d.id === id);
  if (idx === -1) return;
  drafts[idx] = { ...drafts[idx], ...updates };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(drafts));
}

export function deleteDraft(id: string): void {
  const drafts = loadDrafts().filter((d) => d.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(drafts));
}
