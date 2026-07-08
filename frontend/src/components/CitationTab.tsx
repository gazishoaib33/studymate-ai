import { Citation } from "../lib/api";

export default function CitationTab({ citation, index }: { citation: Citation; index: number }) {
  return (
    <details className="group relative inline-block">
      <summary
        className="focus-ring list-none cursor-pointer select-none inline-flex items-center gap-1
                   bg-brass/15 hover:bg-brass/25 text-brass-dark border border-brass/40
                   rounded-t-sm rounded-br-sm px-2 py-0.5 text-xs font-mono transition-colors"
        style={{
          clipPath: "polygon(0 0, 100% 0, 100% 100%, 6% 100%, 0 70%)",
        }}
      >
        <span>#{index + 1}</span>
        {citation.page !== null && <span className="opacity-70">p.{citation.page}</span>}
      </summary>
      <div className="absolute z-10 mt-1 w-64 rounded-md border border-border bg-paper-card p-3 text-xs text-ink-soft shadow-lg">
        {citation.text_preview}
        {citation.text_preview.length >= 200 && "…"}
      </div>
    </details>
  );
}
