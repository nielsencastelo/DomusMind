export function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span className="relative inline-flex h-3 w-3 flex-shrink-0">
      <span
        className="absolute inline-flex h-full w-full rounded-full opacity-60"
        style={{
          background: ok ? "var(--good)" : "var(--bad)",
          animation: `${ok ? "pulse-ring" : "pulse-ring-bad"} 2.2s ease-in-out infinite`,
        }}
      />
      <span
        className="relative inline-flex h-3 w-3 rounded-full"
        style={{
          background: ok ? "var(--good)" : "var(--bad)",
          boxShadow: ok ? "0 0 8px var(--good)" : "0 0 8px var(--bad)",
        }}
      />
    </span>
  );
}
