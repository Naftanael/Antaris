export function runAccessibilityChecks(sourceCode: string): string[] {
  const issues: string[] = [];

  if (!sourceCode.includes("LoadingState")) {
    issues.push("Missing LoadingState handling.");
  }

  if (!sourceCode.includes("EmptyState")) {
    issues.push("Missing EmptyState handling.");
  }

  if (!sourceCode.includes("ErrorState")) {
    issues.push("Missing ErrorState handling.");
  }

  if (!sourceCode.includes("aria-label") && !sourceCode.includes("aria-labelledby")) {
    issues.push("No aria-label or aria-labelledby found.");
  }

  if (!sourceCode.includes("label=")) {
    issues.push("Interactive controls are missing visible labels.");
  }

  return issues;
}
