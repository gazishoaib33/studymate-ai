import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Header from "../components/Header";
import { createChat, Document, DocumentStatus, getDocument, listDocuments, uploadDocument } from "../lib/api";

const STATUS_LABEL: Record<DocumentStatus, string> = {
  uploaded: "Queued",
  processing: "Reading…",
  ready: "Ready",
  failed: "Failed",
};

const STATUS_STYLE: Record<DocumentStatus, string> = {
  uploaded: "bg-ink-soft/10 text-ink-soft",
  processing: "bg-brass/15 text-brass-dark",
  ready: "bg-pine/15 text-pine-dark",
  failed: "bg-red-50 text-red-700",
};

export default function SubjectPage() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<number | null>(null);

  const refresh = useCallback(() => {
    if (!subjectId) return;
    listDocuments(subjectId)
      .then(setDocuments)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [subjectId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll any documents still processing, so status updates without a manual refresh
  useEffect(() => {
    const hasPending = documents.some((d) => d.status === "uploaded" || d.status === "processing");
    if (!hasPending) return;

    pollRef.current = window.setInterval(async () => {
      const updated = await Promise.all(
        documents.map((d) => (d.status === "ready" || d.status === "failed" ? d : getDocument(d.id)))
      );
      setDocuments(updated as Document[]);
    }, 3000);

    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [documents]);

  async function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !subjectId) return;
    setUploading(true);
    setError(null);
    try {
      const doc = await uploadDocument(subjectId, file);
      setDocuments((prev) => [doc, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleChat(documentId: string) {
    try {
      const chat = await createChat(documentId);
      navigate(`/chat/${chat.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start chat");
    }
  }

  return (
    <div>
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-12">
        <div className="mb-10 flex items-center justify-between">
          <h2 className="font-display text-3xl font-semibold text-ink">Lecture notes</h2>
          <label className="focus-ring cursor-pointer rounded-md bg-brass px-5 py-2 font-body text-sm font-medium text-paper-card transition-colors hover:bg-brass-dark">
            {uploading ? "Uploading…" : "Upload PDF"}
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              disabled={uploading}
              onChange={handleFileChange}
            />
          </label>
        </div>

        {error && <p className="mb-6 rounded-md bg-red-50 px-3 py-2 font-body text-sm text-red-700">{error}</p>}

        {loading ? (
          <p className="font-body text-sm text-ink-soft">Loading…</p>
        ) : documents.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border bg-paper-card/50 px-6 py-16 text-center">
            <p className="font-display text-lg text-ink">No lecture PDFs yet</p>
            <p className="mt-1 font-body text-sm text-ink-soft">Upload one to start asking it questions.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between rounded-lg border border-border bg-paper-card px-5 py-4 shadow-sm"
              >
                <div className="min-w-0">
                  <p className="truncate font-body text-sm font-medium text-ink">{doc.filename}</p>
                  <div className="mt-1.5 flex items-center gap-2">
                    <span
                      className={`rounded-full px-2.5 py-0.5 font-mono text-[11px] uppercase tracking-wide ${STATUS_STYLE[doc.status]}`}
                    >
                      {STATUS_LABEL[doc.status]}
                    </span>
                    {doc.page_count && (
                      <span className="font-mono text-[11px] text-ink-soft">{doc.page_count} pages</span>
                    )}
                  </div>
                </div>
                <div className="ml-4 flex shrink-0 gap-2">
                  <button
                    onClick={() => navigate(`/study/${doc.id}`)}
                    disabled={doc.status !== "ready"}
                    className="focus-ring rounded-md border border-brass px-4 py-1.5 font-body text-sm font-medium text-brass-dark transition-colors hover:bg-brass hover:text-paper-card disabled:cursor-not-allowed disabled:border-border disabled:text-ink-soft/40 disabled:hover:bg-transparent"
                  >
                    Study
                  </button>
                  <button
                    onClick={() => handleChat(doc.id)}
                    disabled={doc.status !== "ready"}
                    className="focus-ring rounded-md border border-pine px-4 py-1.5 font-body text-sm font-medium text-pine transition-colors hover:bg-pine hover:text-paper-card disabled:cursor-not-allowed disabled:border-border disabled:text-ink-soft/40 disabled:hover:bg-transparent"
                  >
                    Chat
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
