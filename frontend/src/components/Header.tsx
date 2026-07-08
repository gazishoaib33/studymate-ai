import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

export default function Header() {
  const { email, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="border-b border-border bg-paper-card">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-baseline gap-2 group">
          <span className="font-display text-2xl font-semibold tracking-tight text-ink">
            StudyMate
          </span>
          <span className="font-mono text-[10px] uppercase tracking-widest text-brass-dark border border-brass/40 rounded-sm px-1.5 py-0.5">
            AI
          </span>
        </Link>
        {email && (
          <div className="flex items-center gap-4">
            <span className="font-body text-sm text-ink-soft hidden sm:inline">{email}</span>
            <button
              onClick={handleLogout}
              className="focus-ring font-body text-sm text-ink-soft hover:text-ink border border-border rounded-full px-4 py-1.5 hover:border-ink/30 transition-colors"
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
