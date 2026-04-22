export function runLayoutChecks(sourceCode: string): string[] {
  const issues: string[] = [];

  if (sourceCode.includes("w-screen") && !sourceCode.includes("overflow-x-hidden")) {
    issues.push("Potential horizontal overflow due to w-screen without overflow guard.");
  }

  if (!sourceCode.includes("max-w-")) {
    issues.push("Container has no max-width constraint.");
  }

  if (!sourceCode.includes("space-y-") && !sourceCode.includes("gap-")) {
    issues.push("Layout spacing utilities not found.");
  }

  return issues;
}
