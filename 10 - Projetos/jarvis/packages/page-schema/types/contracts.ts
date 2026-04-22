import type { z } from "zod";
import {
  ActionSchema,
  CompositionPlanSchema,
  PageIntentSchema,
  PageSchema,
  ReviewReportSchema,
  SectionSchema,
  VisualTestReportSchema,
} from "../zod/contracts.js";

export type PageIntent = z.infer<typeof PageIntentSchema>;
export type PageSection = z.infer<typeof SectionSchema>;
export type PageAction = z.infer<typeof ActionSchema>;
export type PageSchemaType = z.infer<typeof PageSchema>;
export type CompositionPlan = z.infer<typeof CompositionPlanSchema>;
export type ReviewReport = z.infer<typeof ReviewReportSchema>;
export type VisualTestReport = z.infer<typeof VisualTestReportSchema>;
