const API_BASE = "http://localhost:8000/api/v1";

function getToken(): string | null {
  return localStorage.getItem("studymate_token");
}

export function setToken(token: string) {
  localStorage.setItem("studymate_token", token);
}

export function clearToken() {
  localStorage.removeItem("studymate_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && options.body) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* ignore parse failure */
    }
    throw new Error(detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- Types ---
export interface User {
  id: string;
  email: string;
  full_name: string | null;
}

export interface Subject {
  id: string;
  name: string;
  created_at: string;
}

export type DocumentStatus = "uploaded" | "processing" | "ready" | "failed";

export interface Document {
  id: string;
  subject_id: string;
  filename: string;
  status: DocumentStatus;
  page_count: number | null;
  created_at: string;
}

export interface Chat {
  id: string;
  document_id: string;
  title: string;
  created_at: string;
}

export interface Citation {
  chunk_id: string;
  page: number | null;
  text_preview: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  created_at: string;
}

// --- Auth ---
export async function register(email: string, password: string, fullName?: string): Promise<User> {
  return request<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName || null }),
  });
}

export async function login(email: string, password: string): Promise<string> {
  const data = await request<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data.access_token;
}

// --- Subjects ---
export async function listSubjects(): Promise<Subject[]> {
  return request<Subject[]>("/subjects/");
}

export async function createSubject(name: string): Promise<Subject> {
  return request<Subject>("/subjects/", { method: "POST", body: JSON.stringify({ name }) });
}

// --- Documents ---
export async function listDocuments(subjectId: string): Promise<Document[]> {
  return request<Document[]>(`/documents/?subject_id=${subjectId}`);
}

export async function uploadDocument(subjectId: string, file: File): Promise<Document> {
  const form = new FormData();
  form.append("subject_id", subjectId);
  form.append("file", file);
  return request<Document>("/documents/upload", { method: "POST", body: form });
}

export async function getDocument(documentId: string): Promise<Document> {
  return request<Document>(`/documents/${documentId}`);
}

export interface Flashcard {
  id: string;
  question: string;
  answer: string;
  created_at: string;
}

export interface QuizQuestion {
  question: string;
  type: "mcq" | "true_false" | "short_answer";
  options?: string[];
  correct_answer: string;
  explanation?: string;
}

export interface Quiz {
  id: string;
  title: string;
  difficulty: string;
  questions: QuizQuestion[];
  created_at: string;
}

export interface QuizAttemptResult {
  id: string;
  score: number;
  total: number;
  created_at: string;
}

// --- Chats ---
export async function listChats(): Promise<Chat[]> {
  return request<Chat[]>("/chat/");
}

export async function createChat(documentId: string, title?: string): Promise<Chat> {
  return request<Chat>("/chat/", { method: "POST", body: JSON.stringify({ document_id: documentId, title }) });
}

export async function getMessages(chatId: string): Promise<Message[]> {
  return request<Message[]>(`/chat/${chatId}/messages`);
}

// --- Study tools ---
export async function generateSummary(documentId: string, mode: "bullets" | "paragraphs" = "bullets"): Promise<{ summary: string }> {
  return request(`/documents/${documentId}/summary`, { method: "POST", body: JSON.stringify({ mode }) });
}

export async function getCachedSummary(documentId: string): Promise<{ summary: string }> {
  return request(`/documents/${documentId}/summary`);
}

export async function generateFlashcards(documentId: string, count = 10): Promise<Flashcard[]> {
  return request(`/documents/${documentId}/flashcards`, { method: "POST", body: JSON.stringify({ count }) });
}

export async function listFlashcards(documentId: string): Promise<Flashcard[]> {
  return request(`/documents/${documentId}/flashcards`);
}

export async function generateQuiz(documentId: string, difficulty: "easy" | "medium" | "hard", count = 5): Promise<Quiz> {
  return request(`/documents/${documentId}/quiz`, { method: "POST", body: JSON.stringify({ difficulty, count }) });
}

export async function submitQuizAttempt(quizId: string, answers: Record<string, string>): Promise<QuizAttemptResult> {
  return request(`/documents/quiz/${quizId}/attempt`, { method: "POST", body: JSON.stringify({ answers }) });
}
export interface StreamEvent {
  type: "citations" | "token" | "done";
  citations?: Citation[];
  content?: string;
}

export async function* streamMessage(chatId: string, content: string): AsyncGenerator<StreamEvent> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/chat/${chatId}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ content }),
  });

  if (!res.ok || !res.body) {
    throw new Error(`Chat request failed: ${res.statusText}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const jsonStr = trimmed.slice(5).trim();
      if (!jsonStr) continue;
      yield JSON.parse(jsonStr) as StreamEvent;
    }
  }
}
