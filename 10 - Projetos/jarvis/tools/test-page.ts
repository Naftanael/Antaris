#!/usr/bin/env node
import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import { VisualTestReportSchema } from "../packages/page-schema/zod/contracts.js";
import { runPlaywrightVisualAudit } from "../packages/visual-tests/playwright/runner.js";

type CliArgs = {
  pagePath?: string;
  url?: string;
  out?: string;
  updateBaseline: boolean;
  strictSnapshots: boolean;
  snapshotThresholdPercent: number;
  snapshotDir?: string;
  screenshotDir?: string;
  pageId?: string;
};

async function fileExists(candidatePath: string): Promise<boolean> {
  try {
    await access(candidatePath);
    return true;
  } catch {
    return false;
  }
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

function parseNumber(raw: string | undefined, fallback: number): number {
  if (!raw) {
    return fallback;
  }
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = {
    updateBaseline: false,
    strictSnapshots: true,
    snapshotThresholdPercent: 0.3,
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

    if (token === "--update-baseline") {
      args.updateBaseline = true;
      continue;
    }

    if (token === "--allow-missing-baseline") {
      args.strictSnapshots = false;
      continue;
    }
  }

  if (!args.pagePath && !args.url) {
    throw new Error(
      "Uso: npm run test-page -- --page <generated-page.tsx> [--url <http|file://...>] [--out visual-report.json]"
    );
  }

  return args;
}

async function inferTargetUrl(args: CliArgs): Promise<string> {
  if (args.url) {
    return args.url;
  }

  if (!args.pagePath) {
    throw new Error("Nao foi possivel inferir URL alvo sem --page ou --url.");
  }

  const pagePath = path.resolve(args.pagePath);
  const previewPath = path.join(path.dirname(pagePath), "preview.html");

  if (!(await fileExists(previewPath))) {
    throw new Error(
      `preview.html nao encontrado para testes reais. Gere novamente a pagina ou informe --url. Esperado: ${previewPath}`
    );
  }

  return `file://${previewPath}`;
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
        // Ignore parse errors and fallback below.
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

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  const url = await inferTargetUrl(args);
  const pageId = await inferPageId(args);

  const snapshotDir = path.resolve(args.snapshotDir ?? path.join("packages", "visual-tests", "snapshots"));
  const defaultScreenshotDir = path.resolve(
    path.join(".artifacts", "reports", "screenshots", `${pageId}-${runId()}`)
  );
  const screenshotDir = path.resolve(args.screenshotDir ?? defaultScreenshotDir);

  await mkdir(screenshotDir, { recursive: true });

  const visualAudit = await runPlaywrightVisualAudit({
    url,
    pageId,
    snapshotDir,
    screenshotDir,
    updateBaseline: args.updateBaseline,
    strictSnapshots: args.strictSnapshots,
    snapshotThresholdPercent: args.snapshotThresholdPercent,
  });

  const failedViewports = visualAudit.viewportResults.filter((result) => result.status === "failed");
  const report = VisualTestReportSchema.parse({
    passed:
      failedViewports.length === 0 &&
      visualAudit.a11yIssues.length === 0 &&
      visualAudit.layoutIssues.length === 0,
    viewportResults: visualAudit.viewportResults.map((result) => ({
      viewport: result.viewport,
      status: result.status,
      issues: result.issues,
    })),
    a11yIssues: visualAudit.a11yIssues,
    layoutIssues: visualAudit.layoutIssues,
    snapshotDiffPercent: visualAudit.snapshotDiffPercent,
  });

  if (args.out) {
    const outPath = path.resolve(args.out);
    await writeFile(outPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
    console.log(`Visual test report written to: ${outPath}`);
  } else {
    console.log(JSON.stringify(report, null, 2));
  }

  console.log(`Screenshots directory: ${screenshotDir}`);
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exit(1);
});
