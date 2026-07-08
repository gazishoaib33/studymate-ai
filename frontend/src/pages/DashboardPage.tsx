import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Header from "../components/Header";
import { createSubject, listSubjects, Subject } from "../lib/api";

export default function DashboardPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSubjects()
      .then(setSubjects)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const subject = await createSubject(newName.trim());
      setSubjects((prev) => [subject, ...prev]);
      setNewName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create subject");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-12">
        <div className="mb-10 flex items-end justify-between">
          <div>
            <h2 className="font-display text-3xl font-semibold text-ink">Your shelf</h2>
            <p className="mt-1 font-body text-sm text-ink-soft">Every subject keeps its own set of lecture notes.</p>
          </div>
        </div>

        <form onSubmit={handleCreate} className="mb-10 flex gap-3">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="New subject, e.g. Data Structures"
            className="focus-ring flex-1 rounded-md border border-border bg-paper-card px-3 py-2 font-body text-sm text-ink placeholder:text-ink-soft/50"
          />
          <button
            type="submit"
            disabled={creating}
            className="focus-ring rounded-md bg-brass px-5 py-2 font-body text-sm font-medium text-paper-card transition-colors hover:bg-brass-dark disabled:opacity-60"
          >
            {creating ? "Adding…" : "Add subject"}
          </button>
        </form>

        {error && <p className="mb-6 rounded-md bg-red-50 px-3 py-2 font-body text-sm text-red-700">{error}</p>}

        {loading ? (
          <p className="font-body text-sm text-ink-soft">Loading your subjects…</p>
        ) : subjects.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border bg-paper-card/50 px-6 py-16 text-center">
            <p className="font-display text-lg text-ink">No subjects yet</p>
            <p className="mt-1 font-body text-sm text-ink-soft">
              Add one above to start uploading lecture PDFs.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {subjects.map((subject) => (
              <Link
                key={subject.id}
                to={`/subjects/${subject.id}`}
                className="focus-ring group rounded-lg border border-border bg-paper-card p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="mb-3 h-1 w-10 rounded-full bg-pine transition-all group-hover:w-16" />
                <h3 className="font-display text-lg font-medium text-ink">{subject.name}</h3>
                <p className="mt-1 font-mono text-xs text-ink-soft">
                  since {new Date(subject.created_at).toLocaleDateString()}
                </p>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
