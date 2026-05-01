"use client";

import { useDomusStore } from "@/lib/store";
import pt from "@/i18n/pt.json";
import en from "@/i18n/en.json";
import es from "@/i18n/es.json";

type Locale = "pt" | "en" | "es";
type Translations = typeof pt;
type TranslationKey = keyof Translations;

const dictionaries: Record<Locale, Translations> = { pt, en, es };

export function useI18n() {
  const locale = useDomusStore((s) => s.locale) as Locale;
  const dict = dictionaries[locale] ?? dictionaries.pt;

  function t(key: TranslationKey, fallback?: string): string {
    return (dict[key] as string | undefined) ?? fallback ?? key;
  }

  return { t, locale };
}
