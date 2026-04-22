import type { PageIntent, PageSchemaType } from "../page-schema/types/contracts.js";

type RecipeFactory = (intent: PageIntent) => Omit<PageSchemaType, "pageId">;

export const allowedSectionTypes = [
  "metrics-row",
  "tabs-section",
  "activity-feed",
  "filters-bar",
  "table-section",
  "settings-groups",
  "form-section",
  "detail-header",
  "detail-tabs",
] as const;

const baseStates = ["loading", "empty", "error"] as const;

const dashboardRecipe: RecipeFactory = () => ({
  pageType: "dashboard",
  stylePreset: "technical-dark",
  layout: {
    sidebar: true,
    header: true,
    density: "medium",
    maxWidth: "full",
  },
  sections: [
    {
      id: "top-metrics",
      type: "metrics-row",
      title: "KPI Overview",
      components: [
        { type: "metric-card", label: "Agents Active", dataKey: "agents.active" },
        { type: "metric-card", label: "Tasks Running", dataKey: "tasks.running" },
        { type: "metric-card", label: "CPU", dataKey: "system.cpu" },
        { type: "metric-card", label: "Memory", dataKey: "system.memory" },
      ],
    },
    {
      id: "main-tabs",
      type: "tabs-section",
      tabs: ["Overview", "Agents", "Logs", "Network"],
    },
    {
      id: "event-feed",
      type: "activity-feed",
      dataKey: "events.recent",
      title: "Recent Events",
    },
  ],
  states: [...baseStates],
  actions: [
    { id: "refresh", label: "Refresh", variant: "primary" },
    { id: "export", label: "Export", variant: "secondary" },
  ],
});

const tableWithFiltersRecipe: RecipeFactory = () => ({
  pageType: "table",
  stylePreset: "editorial-light",
  layout: {
    sidebar: false,
    header: true,
    density: "medium",
    maxWidth: "xl",
  },
  sections: [
    {
      id: "filters",
      type: "filters-bar",
      title: "Filters",
      components: [
        { type: "select", label: "Status", dataKey: "filters.status" },
        { type: "input", label: "Search", dataKey: "filters.query" },
      ],
    },
    {
      id: "results-table",
      type: "table-section",
      title: "Results",
      dataKey: "table.rows",
    },
  ],
  states: [...baseStates],
  actions: [
    { id: "create", label: "Create", variant: "primary" },
    { id: "clear-filters", label: "Clear filters", variant: "ghost" },
  ],
});

const settingsRecipe: RecipeFactory = () => ({
  pageType: "settings",
  stylePreset: "clinical-clean",
  layout: {
    sidebar: true,
    header: true,
    density: "low",
    maxWidth: "lg",
  },
  sections: [
    {
      id: "settings-groups",
      type: "settings-groups",
      title: "Configuration",
      components: [
        { type: "tabs", label: "General/Security/Notifications", dataKey: "settings.tabs" },
      ],
    },
  ],
  states: [...baseStates],
  actions: [
    { id: "save-settings", label: "Save changes", variant: "primary" },
    { id: "reset-settings", label: "Reset", variant: "secondary" },
  ],
});

const formCrudRecipe: RecipeFactory = () => ({
  pageType: "form",
  stylePreset: "clinical-clean",
  layout: {
    sidebar: false,
    header: true,
    density: "medium",
    maxWidth: "md",
  },
  sections: [
    {
      id: "crud-form",
      type: "form-section",
      title: "Record details",
      components: [
        { type: "input", label: "Name", dataKey: "form.name" },
        { type: "input", label: "Description", dataKey: "form.description" },
        { type: "select", label: "Status", dataKey: "form.status" },
      ],
    },
  ],
  states: [...baseStates],
  actions: [
    { id: "save", label: "Save", variant: "primary" },
    { id: "cancel", label: "Cancel", variant: "secondary" },
  ],
});

const detailWithTabsRecipe: RecipeFactory = () => ({
  pageType: "detail",
  stylePreset: "editorial-light",
  layout: {
    sidebar: false,
    header: true,
    density: "medium",
    maxWidth: "xl",
  },
  sections: [
    {
      id: "detail-header",
      type: "detail-header",
      title: "Entity summary",
      components: [{ type: "badge", label: "Active", dataKey: "entity.status" }],
    },
    {
      id: "detail-tabs",
      type: "detail-tabs",
      tabs: ["Overview", "History", "Related"],
    },
  ],
  states: [...baseStates],
  actions: [
    { id: "edit", label: "Edit", variant: "primary" },
    { id: "archive", label: "Archive", variant: "danger" },
  ],
});

export const recipesByPageType: Record<PageIntent["pageType"], RecipeFactory> = {
  dashboard: dashboardRecipe,
  table: tableWithFiltersRecipe,
  settings: settingsRecipe,
  form: formCrudRecipe,
  detail: detailWithTabsRecipe,
  chat: dashboardRecipe,
};

export const supportedPageRecipes = [
  "dashboard",
  "table",
  "settings",
  "form",
  "detail",
] as const;
