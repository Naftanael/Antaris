import { analyzeIntent } from "./intent-analyzer.js";
import { composeFrontend } from "./frontend-composer.js";
import { resolveDesignSystem } from "./ds-resolver.js";
import { buildPageSchema } from "./schema-builder.js";
import { validatePipeline } from "./validator.js";

export type RunPipelineOptions = {
  stylePreset?: "technical-dark" | "editorial-light" | "clinical-clean";
};

export function runPhase1Pipeline(prompt: string, options: RunPipelineOptions = {}) {
  const intent = analyzeIntent(prompt);
  let schema = buildPageSchema(intent);

  if (options.stylePreset) {
    schema = {
      ...schema,
      stylePreset: options.stylePreset,
    };
  }

  const compositionPlan = resolveDesignSystem(schema);
  const sourceCode = composeFrontend(schema, compositionPlan);
  const validation = validatePipeline(intent, schema, compositionPlan, sourceCode);

  if (!validation.ok) {
    const details = validation.issues.map((issue) => `${issue.code}: ${issue.message}`).join("\n");
    throw new Error(`Pipeline validation failed:\n${details}`);
  }

  return {
    intent,
    schema,
    compositionPlan,
    sourceCode,
    validation,
  };
}
