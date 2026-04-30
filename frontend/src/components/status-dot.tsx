export function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${
        ok ? "bg-[var(--good)]" : "bg-[var(--bad)]"
      }`}
    />
  );
}
