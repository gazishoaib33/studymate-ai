import { FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Header from "../components/Header";
import CitationTab from "../components/CitationTab";
import { Citation, getMessages, Message, streamMessage } from "../lib/api";

interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
}

export default function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chatId) return;
    getMessages(chatId)
      .then((msgs: Message[]) =>
        setMessages(msgs.map((m) => ({ id: m.id, role: m.role, content: m.content, citations: m.citations })))
      )
      .catch((err) => setError(err.message));
  }, [chatId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || !chatId || sending) return;

    setInput("");
    setError(null);
    setSending(true);

    const userMsgId = `local-user-${Date.now()}`;
    const assistantMsgId = `local-assistant-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: question, citations: null },
      { id: assistantMsgId, role: "assistant", content: "", citations: null },
    ]);

    try {
      for await (const event of streamMessage(chatId, question)) {
        if (event.type === "citations") {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsgId ? { ...m, citations: event.citations || [] } : m))
          );
        } else if (event.type === "token") {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsgId ? { ...m, content: m.content + (event.content || "") } : m))
          );
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "The connection dropped -- try asking again.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex h-screen flex-col">
      <Header />
      <div className="flex items-center gap-3 border-b border-border bg-paper-card/60 px-6 py-3">
        <button
          onClick={() => navigate(-1)}
          className="focus-ring font-body text-sm text-ink-soft hover:text-ink"
        >
          ← Back
        </button>
        <span className="font-mono text-xs text-ink-soft">Ask anything about this document</span>
      </div>

      <main className="flex-1 overflow-y-auto px-6 py-8">
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.length === 0 && (
            <div className="rounded-lg border border-dashed border-border bg-paper-card/50 px-6 py-12 text-center">
              <p className="font-display text-lg text-ink">Start the conversation</p>
              <p className="mt-1 font-body text-sm text-ink-soft">
                Ask about a concept, request a simpler explanation, or quiz yourself.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={msg.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div
                className={
                  msg.role === "user"
                    ? "max-w-[80%] rounded-2xl rounded-br-sm bg-pine px-4 py-3 font-body text-sm text-paper-card"
                    : "max-w-[80%] rounded-2xl rounded-bl-sm border border-border bg-paper-card px-4 py-3 font-body text-sm text-ink"
                }
              >
                <p className="whitespace-pre-wrap leading-relaxed">
                  {msg.content || (msg.role === "assistant" && sending ? "…" : "")}
                </p>
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5 border-t border-border/60 pt-2">
                    {msg.citations.map((c, i) => (
                      <CitationTab key={c.chunk_id} citation={c} index={i} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </main>

      {error && (
        <p className="mx-6 mb-2 rounded-md bg-red-50 px-3 py-2 font-body text-sm text-red-700">{error}</p>
      )}

      <form onSubmit={handleSubmit} className="border-t border-border bg-paper-card px-6 py-4">
        <div className="mx-auto flex max-w-3xl gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about this lecture…"
            disabled={sending}
            className="focus-ring flex-1 rounded-full border border-border bg-paper px-4 py-2.5 font-body text-sm text-ink placeholder:text-ink-soft/50"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="focus-ring rounded-full bg-brass px-6 py-2.5 font-body text-sm font-medium text-paper-card transition-colors hover:bg-brass-dark disabled:opacity-50"
          >
            {sending ? "Thinking…" : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}
