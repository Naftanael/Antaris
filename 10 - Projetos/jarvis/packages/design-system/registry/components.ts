export type ComponentDefinition = {
  name: string;
  purpose: string;
  requiredProps: string[];
  optionalProps: string[];
  allowedVariants: string[];
  supportedStates: Array<"default" | "loading" | "empty" | "error" | "disabled">;
  forbiddenUses: string[];
  validExamples: string[];
};

const definitions: ComponentDefinition[] = [
  {
    name: "Button",
    purpose: "Primary and secondary actions.",
    requiredProps: ["label", "onClick"],
    optionalProps: ["variant", "size", "icon"],
    allowedVariants: ["primary", "secondary", "ghost", "danger"],
    supportedStates: ["default", "disabled", "loading"],
    forbiddenUses: ["Dense paragraph content", "Status-only communication"],
    validExamples: ["Save settings", "Refresh dashboard"],
  },
  {
    name: "Card",
    purpose: "Grouped content container.",
    requiredProps: ["children"],
    optionalProps: ["title", "description", "footer"],
    allowedVariants: ["default", "elevated", "outline"],
    supportedStates: ["default", "loading", "empty", "error"],
    forbiddenUses: ["Deep nested interactive trees"],
    validExamples: ["Summary section", "Profile block"],
  },
  {
    name: "Input",
    purpose: "Single-line form entry.",
    requiredProps: ["name", "label"],
    optionalProps: ["placeholder", "value", "errorMessage", "helperText"],
    allowedVariants: ["default", "filled"],
    supportedStates: ["default", "disabled", "error"],
    forbiddenUses: ["Large multi-line text"],
    validExamples: ["Email", "Project name"],
  },
  {
    name: "Select",
    purpose: "Choice from constrained options.",
    requiredProps: ["name", "label", "options"],
    optionalProps: ["value", "placeholder"],
    allowedVariants: ["default"],
    supportedStates: ["default", "disabled", "error"],
    forbiddenUses: ["Unbounded free text input"],
    validExamples: ["Status filter", "Role selector"],
  },
  {
    name: "Dialog",
    purpose: "Focused modal interaction.",
    requiredProps: ["title", "children"],
    optionalProps: ["description", "footerActions"],
    allowedVariants: ["default", "confirmation"],
    supportedStates: ["default", "loading", "error"],
    forbiddenUses: ["Long-form page layout"],
    validExamples: ["Delete confirmation", "Quick edit"],
  },
  {
    name: "Tabs",
    purpose: "Segment related views within one page.",
    requiredProps: ["tabs"],
    optionalProps: ["defaultTab"],
    allowedVariants: ["underline", "pill"],
    supportedStates: ["default"],
    forbiddenUses: ["Primary global navigation"],
    validExamples: ["Overview/Logs/Network", "Profile/Security"],
  },
  {
    name: "Badge",
    purpose: "Compact status indicators.",
    requiredProps: ["label"],
    optionalProps: ["variant"],
    allowedVariants: ["neutral", "success", "warning", "danger", "info"],
    supportedStates: ["default"],
    forbiddenUses: ["Primary call-to-action"],
    validExamples: ["Online", "Pending"],
  },
  {
    name: "Table",
    purpose: "Structured tabular data.",
    requiredProps: ["columns", "rows"],
    optionalProps: ["sortable", "pagination"],
    allowedVariants: ["default", "compact"],
    supportedStates: ["default", "loading", "empty", "error"],
    forbiddenUses: ["Narrative content"],
    validExamples: ["Users list", "Task queue"],
  },
  {
    name: "EmptyState",
    purpose: "No-data feedback with guidance.",
    requiredProps: ["title", "description"],
    optionalProps: ["actionLabel", "onAction"],
    allowedVariants: ["default", "illustrated"],
    supportedStates: ["empty"],
    forbiddenUses: ["Represent loading or errors"],
    validExamples: ["No alerts yet", "No results found"],
  },
  {
    name: "LoadingState",
    purpose: "Progress feedback while data is being fetched.",
    requiredProps: ["label"],
    optionalProps: ["skeletonRows"],
    allowedVariants: ["skeleton", "spinner"],
    supportedStates: ["loading"],
    forbiddenUses: ["Long-duration blocking screens without context"],
    validExamples: ["Loading dashboard metrics"],
  },
  {
    name: "ErrorState",
    purpose: "Error feedback with recovery action.",
    requiredProps: ["title", "message"],
    optionalProps: ["actionLabel", "onRetry"],
    allowedVariants: ["inline", "card"],
    supportedStates: ["error"],
    forbiddenUses: ["Success confirmations"],
    validExamples: ["Could not load telemetry"],
  },
  {
    name: "SectionHeader",
    purpose: "Section labeling with context and actions.",
    requiredProps: ["title"],
    optionalProps: ["description", "actions"],
    allowedVariants: ["default", "compact"],
    supportedStates: ["default"],
    forbiddenUses: ["Page-level navigation"],
    validExamples: ["Recent activity", "System settings"],
  },
  {
    name: "MetricCard",
    purpose: "Compact KPI visualization.",
    requiredProps: ["label", "value"],
    optionalProps: ["delta", "icon", "hint"],
    allowedVariants: ["default", "success", "warning", "danger"],
    supportedStates: ["default", "loading"],
    forbiddenUses: ["Long descriptive copy", "Primary actions"],
    validExamples: ["CPU 63%", "Agents Active 12"],
  },
  {
    name: "ActivityFeed",
    purpose: "Chronological events list.",
    requiredProps: ["items"],
    optionalProps: ["maxItems", "showTimestamps"],
    allowedVariants: ["default", "dense"],
    supportedStates: ["default", "loading", "empty", "error"],
    forbiddenUses: ["Hierarchical tree rendering"],
    validExamples: ["Recent agent events", "Audit trail"],
  },
];

export const componentRegistry = definitions;

export const componentRegistryByName = Object.fromEntries(
  definitions.map((definition) => [definition.name, definition])
) as Record<string, ComponentDefinition>;

export const allowedComponentNames = new Set(definitions.map((definition) => definition.name));
