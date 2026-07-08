import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Header from "../components/Header";
import {
  Flashcard,
  Quiz,
  generateFlashcards,
  generateQuiz,
  generateSummary,
  getCachedSummary,
  listFlashcards,
  submitQuizAttempt,
} from "../lib/api";

type Tab = "summary" | "flashcards" | "quiz";

export default function StudyToolsPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("summary");

  return (
    <div>
      <Header />
      <div className="flex items-center gap-3 border-b border-border bg-paper-card/60 px-6 py-3">
        <button onClick={() => navigate(-1)} className="focus-ring font-body text-sm text-ink-soft hover:text-ink">
          ← Back
        </button>
        <span className="font-mono text-xs text-ink-soft">Study tools for this document</span>
      </div>

      <main className="mx-auto max-w-3xl px-6 py-10">
        <div className="mb-8 flex gap-1 rounded-full border border-border bg-paper-card p-1 w-fit">
          {(["summary", "flashcards", "quiz"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`focus-ring rounded-full px-5 py-1.5 font-body text-sm capitalize transition-colors ${
                tab === t ? "bg-pine text-paper-card" : "text-ink-soft hover:text-ink"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {documentId && tab === "summary" && <SummaryTab documentId={documentId} />}
        {documentId && tab === "flashcards" && <FlashcardsTab documentId={documentId} />}
        {documentId && tab === "quiz" && <QuizTab documentId={documentId} />}
      </main>
    </div>
  );
}

function SummaryTab({ documentId }: { documentId: string }) {
  const [summary, setSummary] = useState<string | null>(null);
  const [mode, setMode] = useState<"bullets" | "paragraphs">("bullets");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCachedSummary(documentId)
      .then((res) => setSummary(res.summary))
      .catch(() => {
        /* no cached summary yet -- fine, user can generate one */
      });
  }, [documentId]);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const res = await generateSummary(documentId, mode);
      setSummary(res.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate summary");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setMode("bullets")}
            className={`focus-ring rounded-md px-3 py-1 font-mono text-xs ${mode === "bullets" ? "bg-brass/20 text-brass-dark" : "text-ink-soft"}`}
          >
            Bullets
          </button>
          <button
            onClick={() => setMode("paragraphs")}
            className={`focus-ring rounded-md px-3 py-1 font-mono text-xs ${mode === "paragraphs" ? "bg-brass/20 text-brass-dark" : "text-ink-soft"}`}
          >
            Paragraphs
          </button>
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="focus-ring rounded-md bg-brass px-4 py-1.5 font-body text-sm font-medium text-paper-card hover:bg-brass-dark disabled:opacity-60"
        >
          {loading ? "Summarizing… (can take a minute)" : summary ? "Regenerate" : "Generate summary"}
        </button>
      </div>

      {error && <p className="mb-4 rounded-md bg-red-50 px-3 py-2 font-body text-sm text-red-700">{error}</p>}

      {summary ? (
        <div className="rounded-lg border border-border bg-paper-card p-6 shadow-sm">
          <p className="whitespace-pre-wrap font-body text-sm leading-relaxed text-ink">{summary}</p>
        </div>
      ) : (
        !loading && (
          <div className="rounded-lg border border-dashed border-border bg-paper-card/50 px-6 py-12 text-center">
            <p className="font-body text-sm text-ink-soft">No summary yet -- generate one above.</p>
          </div>
        )
      )}
    </div>
  );
}

function FlashcardsTab({ documentId }: { documentId: string }) {
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [flipped, setFlipped] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listFlashcards(documentId).then(setCards).catch(() => {});
  }, [documentId]);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const newCards = await generateFlashcards(documentId, 10);
      setCards((prev) => [...prev, ...newCards]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate flashcards");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-4 flex justify-end">
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="focus-ring rounded-md bg-brass px-4 py-1.5 font-body text-sm font-medium text-paper-card hover:bg-brass-dark disabled:opacity-60"
        >
          {loading ? "Generating… (can take a minute)" : "Generate 10 flashcards"}
        </button>
      </div>

      {error && <p className="mb-4 rounded-md bg-red-50 px-3 py-2 font-body text-sm text-red-700">{error}</p>}

      {cards.length === 0 && !loading ? (
        <div className="rounded-lg border border-dashed border-border bg-paper-card/50 px-6 py-12 text-center">
          <p className="font-body text-sm text-ink-soft">No flashcards yet -- generate some above.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {cards.map((card) => (
            <button
              key={card.id}
              onClick={() => setFlipped((prev) => ({ ...prev, [card.id]: !prev[card.id] }))}
              className="focus-ring rounded-lg border border-border bg-paper-card p-5 text-left shadow-sm transition-all hover:shadow-md min-h-[120px]"
            >
              <span className="mb-2 block font-mono text-[10px] uppercase tracking-widest text-brass-dark">
                {flipped[card.id] ? "Answer" : "Question"} · tap to flip
              </span>
              <p className="font-body text-sm text-ink">{flipped[card.id] ? card.answer : card.question}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function QuizTab({ documentId }: { documentId: string }) {
  const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard">("medium");
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<{ score: number; total: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setResult(null);
    setAnswers({});
    try {
      const newQuiz = await generateQuiz(documentId, difficulty, 5);
      setQuiz(newQuiz);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate quiz");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    if (!quiz) return;
    try {
      const res = await submitQuizAttempt(quiz.id, answers);
      setResult({ score: res.score, total: res.total });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit quiz");
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div className="flex gap-2">
          {(["easy", "medium", "hard"] as const).map((d) => (
            <button
              key={d}
              onClick={() => setDifficulty(d)}
              className={`focus-ring rounded-md px-3 py-1 font-mono text-xs capitalize ${difficulty === d ? "bg-brass/20 text-brass-dark" : "text-ink-soft"}`}
            >
              {d}
            </button>
          ))}
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="focus-ring rounded-md bg-brass px-4 py-1.5 font-body text-sm font-medium text-paper-card hover:bg-brass-dark disabled:opacity-60"
        >
          {loading ? "Generating… (can take a minute)" : "Generate quiz"}
        </button>
      </div>

      {error && <p className="mb-4 rounded-md bg-red-50 px-3 py-2 font-body text-sm text-red-700">{error}</p>}

      {!quiz && !loading && (
        <div className="rounded-lg border border-dashed border-border bg-paper-card/50 px-6 py-12 text-center">
          <p className="font-body text-sm text-ink-soft">No quiz yet -- pick a difficulty and generate one above.</p>
        </div>
      )}

      {quiz && (
        <div className="space-y-5">
          {quiz.questions.map((q, i) => (
            <div key={i} className="rounded-lg border border-border bg-paper-card p-5 shadow-sm">
              <p className="mb-3 font-body text-sm font-medium text-ink">
                {i + 1}. {q.question}
              </p>

              {q.type === "mcq" && q.options ? (
                <div className="space-y-2">
                  {q.options.map((opt) => (
                    <label key={opt} className="flex cursor-pointer items-center gap-2 font-body text-sm text-ink-soft">
                      <input
                        type="radio"
                        name={`q-${i}`}
                        checked={answers[String(i)] === opt}
                        onChange={() => setAnswers((prev) => ({ ...prev, [String(i)]: opt }))}
                        disabled={!!result}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              ) : q.type === "true_false" ? (
                <div className="flex gap-4">
                  {["True", "False"].map((opt) => (
                    <label key={opt} className="flex cursor-pointer items-center gap-2 font-body text-sm text-ink-soft">
                      <input
                        type="radio"
                        name={`q-${i}`}
                        checked={answers[String(i)] === opt}
                        onChange={() => setAnswers((prev) => ({ ...prev, [String(i)]: opt }))}
                        disabled={!!result}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              ) : (
                <input
                  type="text"
                  value={answers[String(i)] || ""}
                  onChange={(e) => setAnswers((prev) => ({ ...prev, [String(i)]: e.target.value }))}
                  disabled={!!result}
                  placeholder="Your answer"
                  className="focus-ring w-full rounded-md border border-border bg-paper px-3 py-2 font-body text-sm text-ink"
                />
              )}

              {result && (
                <p className="mt-3 border-t border-border/60 pt-2 font-mono text-xs text-pine-dark">
                  Correct answer: {q.correct_answer}
                  {q.explanation && <span className="block text-ink-soft">{q.explanation}</span>}
                </p>
              )}
            </div>
          ))}

          {!result ? (
            <button
              onClick={handleSubmit}
              className="focus-ring rounded-md bg-pine px-5 py-2 font-body text-sm font-medium text-paper-card hover:bg-pine-dark"
            >
              Submit answers
            </button>
          ) : (
            <div className="rounded-lg border border-pine/40 bg-pine/10 px-5 py-4 font-body text-sm text-pine-dark">
              You scored {result.score} / {result.total}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
