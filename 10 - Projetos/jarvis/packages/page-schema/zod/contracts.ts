import { z } from "zod";

export const PageTypeEnum = z.enum([
  "dashboard",
  "form",
  "table",
  "settings",
  "detail",
  "chat",
]);

export const ComplexityEnum = z.enum(["low", "medium", "high"]);

export const PageIntentSchema = z.object({
  goal: z.string().min(1),
  userType: z.string().min(1),
  pageType: PageTypeEnum,
  primaryActions: z.array(z.string()).min(1),
  priorityData: z.array(z.string()).min(1),
  complexity: ComplexityEnum,
});

export const DensityEnum = z.enum(["low", "medium", "high"]);
export const MaxWidthEnum = z.enum(["sm", "md", "lg", "xl", "full"]);

export const ComponentItemSchema = z.object({
  type: z.string().min(1),
  label: z.string().optional(),
  dataKey: z.string().optional(),
  variant: z.string().optional(),
  props: z.record(z.unknown()).optional(),
});

export const SectionSchema = z.object({
  id: z.string().min(1),
  type: z.string().min(1),
  title: z.string().optional(),
  components: z.array(ComponentItemSchema).optional(),
  tabs: z.array(z.string()).optional(),
  dataKey: z.string().optional(),
});

export const ActionSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  variant: z.string().optional(),
});

export const PageSchema = z.object({
  pageId: z.string().min(1),
  pageType: z.string().min(1),
  stylePreset: z.string().min(1),
  layout: z.object({
    sidebar: z.boolean().optional(),
    header: z.boolean().optional(),
    density: DensityEnum,
    maxWidth: MaxWidthEnum,
  }),
  sections: z.array(SectionSchema).min(1),
  states: z.array(z.enum(["loading", "empty", "error"])).min(1),
  actions: z.array(ActionSchema),
});

export const CompositionMappingSchema = z.object({
  abstractType: z.string().min(1),
  concreteComponent: z.string().min(1),
  variant: z.string().optional(),
  propsShape: z.record(z.unknown()).optional(),
});

export const CompositionPlanSchema = z.object({
  pageId: z.string().min(1),
  stylePreset: z.string().min(1),
  sections: z.array(
    z.object({
      sectionId: z.string().min(1),
      layoutNotes: z.array(z.string()).default([]),
      componentMappings: z.array(CompositionMappingSchema).min(1),
    })
  ),
});

const ScoreSchema = z.number().min(0).max(5);

export const ReviewReportSchema = z.object({
  approved: z.boolean(),
  scores: z.object({
    hierarchy: ScoreSchema,
    spacing: ScoreSchema,
    legibility: ScoreSchema,
    accessibility: ScoreSchema,
    responsiveness: ScoreSchema,
    consistency: ScoreSchema,
  }),
  mandatoryFixes: z.array(z.string()),
  optionalFixes: z.array(z.string()),
});

export const VisualTestReportSchema = z.object({
  passed: z.boolean(),
  viewportResults: z.array(
    z.object({
      viewport: z.string(),
      status: z.enum(["passed", "failed"]),
      issues: z.array(z.string()),
    })
  ),
  a11yIssues: z.array(z.string()),
  layoutIssues: z.array(z.string()),
  snapshotDiffPercent: z.number().optional(),
});

export const RequiredDataStates = ["loading", "empty", "error"] as const;
