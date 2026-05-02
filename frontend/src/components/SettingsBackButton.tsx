import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export function SettingsBackButton() {
  return (
    <Link href="/settings" className="btn btn-secondary w-fit px-3 py-2 text-sm">
      <ArrowLeft size={15} />
      Voltar aos ajustes
    </Link>
  );
}

