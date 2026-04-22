import { componentRegistryByName } from "../design-system/registry/index.js";
import { CompositionPlanSchema } from "../page-schema/zod/contracts.js";
import type { CompositionPlan, PageSchemaType } from "../page-schema/types/contracts.js";

const abstractToConcreteComponent: Record<string, string> = {
  "metric-card": "MetricCard",
  tabs: "Tabs",
  "activity-feed": "ActivityFeed",
  table: "Table",
  input: "Input",
  select: "Select",
  badge: "Badge",
};

const sectionTypeDefaults: Record<string, string[]> = {
  "metrics-row": ["MetricCard"],
  "tabs-section": ["Tabs"],
  "activity-feed": ["SectionHeader", "ActivityFeed"],
  "filters-bar": ["SectionHeader", "Select", "Input", "Button"],
  "table-section": ["SectionHeader", "Table"],
  "settings-groups": ["SectionHeader", "Tabs", "Card"],
  "form-section": ["SectionHeader", "Input", "Select", "Button"],
  "detail-header": ["SectionHeader", "Badge", "Card"],
  "detail-tabs": ["Tabs", "Card"],
};

function mapAbstractType(abstractType: string): string {
  const mapped = abstractToConcreteComponent[abstractType] ?? abstractToConcreteComponent[abstractType.toLowerCase()];
  return mapped ?? abstractType;
}

function ensureRegisteredComponent(componentName: string): void {
  if (!componentRegistryByName[componentName]) {
    throw new Error(`Componente fora do registry: ${componentName}`);
  }
}

export function resolveDesignSystem(pageSchema: PageSchemaType): CompositionPlan {
  const sections = pageSchema.sections.map((section) => {
    const componentMappings = [] as CompositionPlan["sections"][number]["componentMappings"];

    if (section.components?.length) {
      for (const component of section.components) {
        const concreteComponent = mapAbstractType(component.type);
        ensureRegisteredComponent(concreteComponent);
        componentMappings.push({
          abstractType: component.type,
          concreteComponent,
          variant: component.variant,
          propsShape: {
            label: component.label,
            dataKey: component.dataKey,
            ...component.props,
          },
        });
      }
    }

    if (!componentMappings.length) {
      const defaults = sectionTypeDefaults[section.type] ?? ["Card"];
      for (const concreteComponent of defaults) {
        ensureRegisteredComponent(concreteComponent);
        componentMappings.push({
          abstractType: section.type,
          concreteComponent,
          variant: "default",
        });
      }
    }

    return {
      sectionId: section.id,
      layoutNotes: [
        `density:${pageSchema.layout.density}`,
        `maxWidth:${pageSchema.layout.maxWidth}`,
        `sectionType:${section.type}`,
      ],
      componentMappings,
    };
  });

  return CompositionPlanSchema.parse({
    pageId: pageSchema.pageId,
    stylePreset: pageSchema.stylePreset,
    sections,
  });
}
