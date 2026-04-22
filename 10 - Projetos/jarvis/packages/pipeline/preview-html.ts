import { themePresets } from "../design-system/themes/presets.js";
import type { CompositionPlan, PageSchemaType } from "../page-schema/types/contracts.js";

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderComponent(name: string, label: string, index: number): string {
  const safeLabel = escapeHtml(label);
  const inputId = `field-${index}-${safeLabel.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;

  if (name === "Button") {
    return `<button class="btn" type="button">${safeLabel}</button>`;
  }

  if (name === "Badge") {
    return `<span class="badge" role="status">${safeLabel}</span>`;
  }

  if (name === "Input") {
    return `<div class="field"><label for="${inputId}">${safeLabel}</label><input id="${inputId}" name="${inputId}" type="text" /></div>`;
  }

  if (name === "Select") {
    return `<div class="field"><label for="${inputId}">${safeLabel}</label><select id="${inputId}" name="${inputId}"><option>Option A</option><option>Option B</option></select></div>`;
  }

  if (name === "Tabs") {
    return `<div class="tabs" role="tablist" aria-label="Section tabs"><button role="tab" aria-selected="true">Overview</button><button role="tab" aria-selected="false">Details</button><button role="tab" aria-selected="false">History</button></div>`;
  }

  if (name === "Table") {
    return `<div class="table-wrap"><table><thead><tr><th>Name</th><th>Status</th><th>Updated</th></tr></thead><tbody><tr><td>Item A</td><td>Active</td><td>Today</td></tr><tr><td>Item B</td><td>Pending</td><td>Yesterday</td></tr></tbody></table></div>`;
  }

  if (name === "MetricCard") {
    return `<article class="metric-card"><p class="metric-label">${safeLabel}</p><p class="metric-value">--</p></article>`;
  }

  if (name === "ActivityFeed") {
    return `<ul class="activity-feed"><li>Event A completed</li><li>Event B started</li><li>Event C failed</li></ul>`;
  }

  if (name === "SectionHeader") {
    return `<h3 class="section-subtitle">${safeLabel}</h3>`;
  }

  return `<div class="chip">${escapeHtml(name)} · ${safeLabel}</div>`;
}

export function buildPreviewHtml(pageSchema: PageSchemaType, compositionPlan: CompositionPlan): string {
  const preset = themePresets[pageSchema.stylePreset as keyof typeof themePresets] ?? themePresets["editorial-light"];

  const actions = pageSchema.actions
    .map((action) => `<button class="btn" type="button">${escapeHtml(action.label)}</button>`)
    .join("\n");

  const sections = compositionPlan.sections
    .map((sectionPlan) => {
      const sectionSchema = pageSchema.sections.find((section) => section.id === sectionPlan.sectionId);
      const sectionTitle = escapeHtml(sectionSchema?.title ?? sectionPlan.sectionId);
      const components = sectionPlan.componentMappings
        .map((mapping, index) => {
          const labelCandidate =
            typeof mapping.propsShape?.label === "string" ? mapping.propsShape.label : sectionTitle;
          return renderComponent(mapping.concreteComponent, String(labelCandidate), index);
        })
        .join("\n");

      return `<section class="section" aria-labelledby="${sectionPlan.sectionId}-title"><h2 id="${sectionPlan.sectionId}-title">${sectionTitle}</h2>${components}</section>`;
    })
    .join("\n");

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${escapeHtml(pageSchema.pageId)}</title>
    <style>
      :root {
        --bg: ${preset.palette.background};
        --surface: ${preset.palette.surface};
        --text: ${preset.palette.text};
        --muted: ${preset.palette.mutedText};
        --border: ${preset.palette.border};
        --primary: ${preset.palette.primary};
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        font-family: "Sora", "Segoe UI", sans-serif;
        background: radial-gradient(circle at 20% 10%, color-mix(in srgb, var(--primary) 10%, transparent), transparent 45%), var(--bg);
        color: var(--text);
      }

      .container {
        width: min(1200px, 100% - 2rem);
        margin-inline: auto;
        padding: 1.25rem 0 2rem;
      }

      header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 1rem;
      }

      h1 {
        margin: 0;
        font-size: clamp(1.25rem, 2vw, 1.75rem);
      }

      .header-actions {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
      }

      .btn {
        appearance: none;
        border: 1px solid var(--border);
        background: var(--surface);
        color: var(--text);
        border-radius: 0.6rem;
        padding: 0.55rem 0.85rem;
        font-weight: 600;
        cursor: pointer;
      }

      .btn:focus-visible,
      .tabs button:focus-visible,
      input:focus-visible,
      select:focus-visible {
        outline: 2px solid var(--primary);
        outline-offset: 2px;
      }

      .section {
        border: 1px solid var(--border);
        background: var(--surface);
        border-radius: 0.9rem;
        padding: 1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.08);
      }

      h2 {
        margin: 0 0 0.75rem;
        font-size: 1.05rem;
      }

      .section-subtitle {
        margin: 0 0 0.5rem;
        font-size: 0.95rem;
        color: var(--muted);
      }

      .metric-card {
        border: 1px solid var(--border);
        border-radius: 0.7rem;
        padding: 0.7rem;
        margin-bottom: 0.5rem;
      }

      .metric-label {
        margin: 0;
        color: var(--muted);
        font-size: 0.88rem;
      }

      .metric-value {
        margin: 0.2rem 0 0;
        font-size: 1.2rem;
        font-weight: 700;
      }

      .activity-feed {
        margin: 0;
        padding-left: 1.2rem;
      }

      .activity-feed li {
        margin-bottom: 0.35rem;
      }

      .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.28rem 0.5rem;
        border: 1px solid var(--border);
        border-radius: 999px;
        background: color-mix(in srgb, var(--primary) 12%, var(--surface));
      }

      .tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }

      .tabs button {
        border: 1px solid var(--border);
        border-radius: 0.6rem;
        background: transparent;
        color: var(--text);
        padding: 0.45rem 0.7rem;
      }

      .field {
        margin-bottom: 0.7rem;
        display: grid;
        gap: 0.35rem;
      }

      label {
        font-weight: 600;
      }

      input,
      select {
        border: 1px solid var(--border);
        border-radius: 0.6rem;
        background: var(--surface);
        color: var(--text);
        padding: 0.55rem 0.7rem;
      }

      .table-wrap {
        overflow-x: auto;
      }

      table {
        width: 100%;
        border-collapse: collapse;
      }

      th,
      td {
        border-bottom: 1px solid var(--border);
        text-align: left;
        padding: 0.55rem;
      }

      .chip {
        display: inline-block;
        border: 1px solid var(--border);
        border-radius: 999px;
        padding: 0.3rem 0.55rem;
        margin-right: 0.35rem;
      }

      @media (max-width: 760px) {
        .container {
          width: calc(100% - 1rem);
        }
      }
    </style>
  </head>
  <body>
    <main class="container" data-page-id="${escapeHtml(pageSchema.pageId)}">
      <header>
        <div>
          <h1>${escapeHtml(pageSchema.pageId)}</h1>
          <p style="margin: 0.4rem 0 0; color: var(--muted)">Preset: ${escapeHtml(pageSchema.stylePreset)}</p>
        </div>
        <div class="header-actions">${actions}</div>
      </header>
      ${sections}
    </main>
  </body>
</html>
`;
}
