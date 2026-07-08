import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <div className="mb-10 text-center">
          <h1 className="font-display text-3xl font-semibold text-ink">StudyMate</h1>
          <p className="mt-2 font-body text-sm text-ink-soft">
            Pick up where your lecture notes leave off.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-lg border border-border bg-paper-card p-8 shadow-sm">
          <div className="space-y-5">
            <div>
              <label className="mb-1.5 block font-body text-sm font-medium text-ink">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="focus-ring w-full rounded-md border border-border bg-paper px-3 py-2 font-body text-sm text-ink placeholder:text-ink-soft/50"
                placeholder="you@university.edu"
              />
            </div>
            <div>
              <label className="mb-1.5 block font-body text-sm font-medium text-ink">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="focus-ring w-full rounded-md border border-border bg-paper px-3 py-2 font-body text-sm text-ink placeholder:text-ink-soft/50"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p className="rounded-md bg-red-50 px-3 py-2 font-body text-sm text-red-700">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="focus-ring w-full rounded-md bg-pine py-2.5 font-body text-sm font-medium text-paper-card transition-colors hover:bg-pine-dark disabled:opacity-60"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </div>
        </form>

        <p className="mt-6 text-center font-body text-sm text-ink-soft">
          New here?{" "}
          <Link to="/register" className="font-medium text-brass-dark hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
