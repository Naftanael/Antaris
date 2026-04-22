import { allowedComponentNames } from "../design-system/registry/index.js";
import { themePresets } from "../design-system/themes/presets.js";
import {
  CompositionPlanSchema,
  PageIntentSchema,
  PageSchema,
  RequiredDataStates,
} from "../page-schema/zod/contracts.js";
import type { CompositionPlan, PageIntent, PageSchemaType } from "../page-schema/types/contracts.js";
import { allowedSectionTypes } from "../ui-recipes/recipes.js";

export type ValidationIssue = {
  code: string;
  message: string;
};

export type PipelineValidation = {
  ok: boolean;
  issues: ValidationIssue[];
};

function hasRequiredDataStates(states: string[]): boolean {
  const set = new Set(states);
  return RequiredDataStates.every((state) => set.has(state));
}

export function validatePipeline(
  intent: PageIntent,
  schema: PageSchemaType,
  compositionPlan: CompositionPlan,
  sourceCode: string
): PipelineValidation {
  const issues: ValidationIssue[] = [];

  if (!PageIntentSchema.safeParse(intent).success) {
    issues.push({ code: "INVALID_INTENT", message: "PageIntent invalido." });
  }

  if (!PageSchema.safeParse(schema).success) {
    issues.push({ code: "INVALID_SCHEMA", message: "PageSchema invalido." });
  }

  if (!CompositionPlanSchema.safeParse(compositionPlan).success) {
    issues.push({ code: "INVALID_COMPOSITION", message: "CompositionPlan invalido." });
  }

  if (!hasRequiredDataStates(schema.states)) {
    issues.push({
      code: "MISSING_STATES",
      message: "PageSchema precisa conter loading, empty e error nos states.",
    });
  }

  if (!themePresets[schema.stylePreset as keyof typeof themePresets]) {
    issues.push({
      code: "INVALID_THEME",
      message: `Theme '${schema.stylePreset}' nao existe entre os presets permitidos.`,
    });
  }

  for (const section of schema.sections) {
    if (!allowedSectionTypes.includes(section.type as (typeof allowedSectionTypes)[number])) {
      issues.push({
        code: "INVALID_SECTION_TYPE",
        message: `Section type '${section.type}' nao permitida pelo recipe registry.`,
      });
    }
  }

  for (const section of compositionPlan.sections) {
    if (!schema.sections.some((candidate) => candidate.id === section.sectionId)) {
      issues.push({
        code: "UNKNOWN_SECTION",
        message: `CompositionPlan referencia sectionId inexistente: ${section.sectionId}.`,
      });
    }

    for (const mapping of section.componentMappings) {
      if (!allowedComponentNames.has(mapping.concreteComponent)) {
        issues.push({
          code: "UNREGISTERED_COMPONENT",
          message: `Componente fora do registry: ${mapping.concreteComponent}.`,
        });
      }
    }
  }

  for (const requiredSignal of ["LoadingState", "EmptyState", "ErrorState"]) {
    if (!sourceCode.includes(requiredSignal)) {
      issues.push({
        code: "MISSING_UI_STATE",
        message: `Codigo gerado sem estado obrigatorio: ${requiredSignal}.`,
      });
    }
  }

  return {
    ok: issues.length === 0,
    issues,
  };
}
