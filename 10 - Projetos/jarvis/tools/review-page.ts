#!/usr/bin/env node
import { access, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import { ReviewReportSchema } from "../packages/page-schema/zod/contracts.js";
import { scoreRubric } from "../packages/ui-evaluator/rubric.js";
import { averageScore } from "../packages/ui-evaluator/score.js";
import { runPlaywrightVisualAudit } from "../packages/visual-tests/playwright/runner.js";

type CliArgs = {
  pagePath?: string;
  url?: string;
  out?: string;
  snapshotDir?: string;
  screenshotDir?: string;
  pageId?: string;
  snapshotThresholdPercent: number;
  strictSnapshots: boolean;
};

type ReviewScores = {
  hierarchy: number;
  spacing: number;
  legibility: number;
  accessibility: number;
  responsiveness: number;
  consistency: number;
};

async function fileExists(candidatePath: string): Promise<boolean> {
  try {
    await access(candidatePath);
    return true;
  } catch {
    return false;
  }
}

function parseNumber(raw: string | undefined, fallback: number): number {
  if (!raw) {
    return fallback;
  }
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function clampScore(value: number): number {
  return Math.max(0, Math.min(5, Number(value.toFixed(1))));
}

function sanitizeId(raw: string): string {
  return raw
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = {
    snapshotThresholdPercent: 0.3,
    strictSnapshots: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];

    if (token === "--page") {
      args.pagePath = argv[index + 1] ?? "";
      index += 1;
      continue;
    }

    if (token === "--url") {
      args.url = argv[index + 1] ?? "";
      index += 1;
      continue;
    }

    if (token === "--out") {
      args.out = argv[index + 1] ?? "";
      index += 1;
      continue;
    }

    if (token === "--snapshot-dir") {
      args.snapshotDir = argv[index + 1] ?? "";
      index += 1;
      continue;
    }

    if (token === "--screenshot-dir") {
      args.screenshotDir = argv[index + 1] ?? "";
      index += 1;
      continue;
    }

    if (token === "--page-id") {
      args.pageId = argv[index + 1] ?? "";
      index += 1;
      continue;
    }

    if (token === "--snapshot-threshold") {
      args.snapshotThresholdPercent = parseNumber(argv[index + 1], 0.3);
      index += 1;
      continue;
    }

    if (token === "--strict-snapshots") {
      args.strictSnapshots = true;
      continue;
    }
  }

  if (!args.pagePath && !args.url) {
    throw new Error(
      "Uso: npm run review-page -- --page <generated-page.tsx> [--url <http|file://...>] [--out review.json]"
    );
  }

  return args;
}

async function inferTargetUrl(args: CliArgs): Promise<string | undefined> {
  if (args.url) {
    return args.url;
  }

  if (!args.pagePath) {
    return undefined;
  }

  const pagePath = path.resolve(args.pagePath);
  const previewPath = path.join(path.dirname(pagePath), "preview.html");

  if (await fileExists(previewPath)) {
    return `file://${previewPath}`;
  }

  return undefined;
}

async function inferPageId(args: CliArgs): Promise<string> {
  if (args.pageId) {
    return sanitizeId(args.pageId);
  }

  if (args.pagePath) {
    const artifactsDir = path.dirname(path.resolve(args.pagePath));
    const schemaPath = path.join(artifactsDir, "page-schema.json");

    if (await fileExists(schemaPath)) {
      try {
        const raw = await readFile(schemaPath, "utf8");
        const parsed = JSON.parse(raw) as { pageId?: string };
        if (parsed.pageId) {
          return sanitizeId(parsed.pageId);
        }
      } catch {
        // Ignore parse errors and fallback.
      }
    }

    return sanitizeId(path.basename(artifactsDir));
  }

  if (args.url) {
    return sanitizeId(args.url);
  }

  return "generated-page";
}

function runId(): string {
  return new Date().toISOString().replace(/[.:]/g, "-");
}

function mergeScores(base: ReviewScores, adjustments: Partial<ReviewScores>): ReviewScores {
  return {
    hierarchy: clampScore(adjustments.hierarchy ?? base.hierarchy),
    spacing: clampScore(adjustments.spacing ?? base.spacing),
    legibility: clampScore(adjustments.legibility ?? base.legibility),
    accessibility: clampScore(adjustments.accessibility ?? base.accessibility),
    responsiveness: clampScore(adjustments.responsiveness ?? base.responsiveness),
    consistency: clampScore(adjustments.consistency ?? base.consistency),
  };
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));

  let sourceCode = "";
  if (args.pagePath) {
    sourceCode = await readFile(path.resolve(args.pagePath), "utf8");
  }

  const baseScores: ReviewScores = sourceCode
    ? scoreRubric(sourceCode)
    : {
        hierarchy: 4,
        spacing: 4,
        legibility: 4,
        accessibility: 4,
        responsiveness: 4,
        consistency: 4,
      };

  const pageId = await inferPageId(args);
  const targetUrl = await inferTargetUrl(args);

  const screenshotDir = path.resolve(
    args.screenshotDir ?? path.join(".artifacts", "reports", "review-screenshots", `${pageId}-${runId()}`)
  );
  const snapshotDir = path.resolve(args.snapshotDir ?? path.join("packages", "visual-tests", "snapshots"));

  let visualMandatoryFixes: string[] = [];
  let accessibilityIssuesCount = 0;
  let failedViewportCount = 0;
  let layoutIssueCount = 0;

  if (targetUrl) {
    const visualAudit = await runPlaywrightVisualAudit({
      url: targetUrl,
      pageId,
      screenshotDir,
      snapshotDir,
      strictSnapshots: args.strictSnapshots,
      updateBaseline: false,
      snapshotThresholdPercent: args.snapshotThresholdPercent,
    });

    visualMandatoryFixes = [...visualAudit.a11yIssues, ...visualAudit.layoutIssues];
    accessibilityIssuesCount = visualAudit.a11yIssues.length;
    layoutIssueCount = visualAudit.layoutIssues.length;
    failedViewportCount = visualAudit.viewportResults.filter((result) => result.status === "failed").length;
  }

  const adjustedScores = mergeScores(baseScores, {
    accessibility: baseScores.accessibility - accessibilityIssuesCount * 0.6,
    responsiveness: baseScores.responsiveness - failedViewportCount * 0.7,
    spacing: baseScores.spacing - layoutIssueCount * 0.2,
    consistency: baseScores.consistency - layoutIssueCount * 0.25,
  });

  const mandatoryFixes = [...new Set(visualMandatoryFixes)];
  const average = averageScore(adjustedScores);

  if (average < 4) {
    mandatoryFixes.push(`Average rubric score ${average} is below 4.0.`);
  }

  if (adjustedScores.accessibility < 4) {
    mandatoryFixes.push(`Accessibility score ${adjustedScores.accessibility} is below 4.0.`);
  }

  const optionalFixes = Object.entries(adjustedScores)
    .filter(([, score]) => score < 4.5)
    .map(([category, score]) => `Improve ${category}: current score ${score}.`);

  if (!targetUrl) {
    optionalFixes.push(
      "Visual audit not executed: provide --url or keep preview.html beside generated-page.tsx for Playwright + axe checks."
    );
  }

  const report = ReviewReportSchema.parse({
    approved: mandatoryFixes.length === 0,
    scores: adjustedScores,
    mandatoryFixes,
    optionalFixes,
  });

  if (args.out) {
    const outPath = path.resolve(args.out);
    await writeFile(outPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
    console.log(`Review report written to: ${outPath}`);
  } else {
    console.log(JSON.stringify(report, null, 2));
  }

  if (targetUrl) {
    console.log(`Review screenshots directory: ${screenshotDir}`);
  }
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exit(1);
});
