export type ThemePresetName = "technical-dark" | "editorial-light" | "clinical-clean";

export type ThemePreset = {
  name: ThemePresetName;
  description: string;
  palette: {
    background: string;
    surface: string;
    text: string;
    mutedText: string;
    border: string;
    primary: string;
  };
};

export const themePresets: Record<ThemePresetName, ThemePreset> = {
  "technical-dark": {
    name: "technical-dark",
    description: "High-contrast observability dashboards.",
    palette: {
      background: "#0b1220",
      surface: "#111a2d",
      text: "#e2e8f0",
      mutedText: "#94a3b8",
      border: "#1f2a44",
      primary: "#22d3ee",
    },
  },
  "editorial-light": {
    name: "editorial-light",
    description: "Readable layouts for content-heavy pages.",
    palette: {
      background: "#fafaf7",
      surface: "#ffffff",
      text: "#1f2937",
      mutedText: "#6b7280",
      border: "#e5e7eb",
      primary: "#2563eb",
    },
  },
  "clinical-clean": {
    name: "clinical-clean",
    description: "Minimal and precise interface for settings/forms.",
    palette: {
      background: "#f8fcff",
      surface: "#ffffff",
      text: "#0f172a",
      mutedText: "#64748b",
      border: "#dbeafe",
      primary: "#0284c7",
    },
  },
};
