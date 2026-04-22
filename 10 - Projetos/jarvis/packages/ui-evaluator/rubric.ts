export type RubricScores = {
  hierarchy: number;
  spacing: number;
  legibility: number;
  accessibility: number;
  responsiveness: number;
  consistency: number;
};

function clampScore(value: number): number {
  return Math.max(0, Math.min(5, Number(value.toFixed(1))));
}

export function scoreRubric(sourceCode: string): RubricScores {
  const hasSectionHeaders = sourceCode.includes("SectionHeader");
  const hasSpacingScale = sourceCode.includes("space-y-") && sourceCode.includes("p-");
  const hasReadableText = sourceCode.includes("text-lg") || sourceCode.includes("text-base");
  const hasA11yStates =
    sourceCode.includes("LoadingState") && sourceCode.includes("EmptyState") && sourceCode.includes("ErrorState");
  const hasResponsiveContainer = sourceCode.includes("max-w-") && sourceCode.includes("w-full");

  return {
    hierarchy: clampScore(hasSectionHeaders ? 4.5 : 2.5),
    spacing: clampScore(hasSpacingScale ? 4.5 : 3),
    legibility: clampScore(hasReadableText ? 4.2 : 3.2),
    accessibility: clampScore(hasA11yStates ? 4.3 : 2.8),
    responsiveness: clampScore(hasResponsiveContainer ? 4.1 : 2.7),
    consistency: clampScore(hasSectionHeaders && hasSpacingScale ? 4.4 : 3.1),
  };
}
