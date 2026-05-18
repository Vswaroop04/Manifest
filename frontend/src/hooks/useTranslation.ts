import en from "@/locales/en.json";

type Translations = typeof en;

function get(obj: unknown, path: string): string {
  const parts = path.split(".");
  let cur: unknown = obj;
  for (const part of parts) {
    if (cur == null || typeof cur !== "object") return path;
    cur = (cur as Record<string, unknown>)[part];
  }
  return typeof cur === "string" ? cur : path;
}

export function useTranslation() {
  function t(key: string, vars?: Record<string, string | number>): string {
    let str = get(en as unknown, key);
    if (vars) {
      Object.entries(vars).forEach(([k, v]) => {
        str = str.replace(`{{${k}}}`, String(v));
      });
    }
    return str;
  }

  return { t, translations: en as Translations };
}
