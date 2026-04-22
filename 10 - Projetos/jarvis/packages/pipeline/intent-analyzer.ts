import { PageIntentSchema } from "../page-schema/zod/contracts.js";
import type { PageIntent } from "../page-schema/types/contracts.js";

const pageTypeMatchers: Array<{ pageType: PageIntent["pageType"]; keywords: string[] }> = [
  {
    pageType: "dashboard",
    keywords: ["dashboard", "metric", "kpi", "telemetry", "painel", "monitor"],
  },
  {
    pageType: "table",
    keywords: ["table", "tabela", "lista", "list", "filtro", "filter", "grid"],
  },
  {
    pageType: "settings",
    keywords: ["settings", "config", "preferencia", "preferences", "configuracao"],
  },
  {
    pageType: "form",
    keywords: ["form", "cadastro", "crud", "create", "edit", "wizard"],
  },
  {
    pageType: "detail",
    keywords: ["detail", "detalhe", "perfil", "profile", "entity", "registro"],
  },
  {
    pageType: "chat",
    keywords: ["chat", "mensagem", "conversation", "conversa"],
  },
];

const primaryActionsByPageType: Record<PageIntent["pageType"], string[]> = {
  dashboard: ["refresh", "export"],
  table: ["filter", "sort", "create"],
  settings: ["save", "reset"],
  form: ["save", "cancel"],
  detail: ["edit", "archive"],
  chat: ["send message", "attach file"],
};

const priorityDataByPageType: Record<PageIntent["pageType"], string[]> = {
  dashboard: ["kpis", "activity", "system_status"],
  table: ["rows", "filters", "pagination"],
  settings: ["preferences", "permissions", "notifications"],
  form: ["field_values", "validation_errors", "metadata"],
  detail: ["entity_summary", "history", "related_records"],
  chat: ["messages", "participants", "attachments"],
};

function detectPageType(promptLower: string): PageIntent["pageType"] {
  for (const matcher of pageTypeMatchers) {
    if (matcher.keywords.some((keyword) => promptLower.includes(keyword))) {
      return matcher.pageType;
    }
  }
  return "dashboard";
}

function detectUserType(promptLower: string): string {
  if (promptLower.includes("admin")) {
    return "admin";
  }
  if (promptLower.includes("analyst") || promptLower.includes("analista")) {
    return "analyst";
  }
  if (promptLower.includes("operator") || promptLower.includes("operador")) {
    return "operator";
  }
  return "internal-user";
}

function detectComplexity(promptLower: string): PageIntent["complexity"] {
  const highSignals = ["real-time", "tempo real", "advanced", "avancado", "multi", "complex"];
  const mediumSignals = ["filters", "filtros", "tabs", "detalhes", "settings"];

  if (highSignals.some((signal) => promptLower.includes(signal))) {
    return "high";
  }

  if (mediumSignals.some((signal) => promptLower.includes(signal))) {
    return "medium";
  }

  return "low";
}

export function analyzeIntent(prompt: string): PageIntent {
  const normalizedPrompt = prompt.trim();
  if (!normalizedPrompt) {
    throw new Error("Prompt vazio: informe a intencao da pagina.");
  }

  const promptLower = normalizedPrompt.toLowerCase();
  const pageType = detectPageType(promptLower);

  const intent: PageIntent = {
    goal: normalizedPrompt.slice(0, 180),
    userType: detectUserType(promptLower),
    pageType,
    primaryActions: primaryActionsByPageType[pageType],
    priorityData: priorityDataByPageType[pageType],
    complexity: detectComplexity(promptLower),
  };

  return PageIntentSchema.parse(intent);
}
