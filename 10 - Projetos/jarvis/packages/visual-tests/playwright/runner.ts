import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import { AxeBuilder } from "@axe-core/playwright";
import pixelmatch from "pixelmatch";
import { chromium, type Page } from "playwright";
import { PNG } from "pngjs";

export type ViewportSpec = {
  name: string;
  width: number;
  height: number;
};

export type ViewportAuditResult = {
  viewport: string;
  status: "passed" | "failed";
  issues: string[];
  screenshotPath: string;
  snapshotDiffPercent?: number;
};

export type PlaywrightVisualAuditResult = {
  viewportResults: ViewportAuditResult[];
  a11yIssues: string[];
  layoutIssues: string[];
  snapshotDiffPercent?: number;
};

export type PlaywrightVisualAuditOptions = {
  url: string;
  pageId: string;
  screenshotDir: string;
  snapshotDir: string;
  updateBaseline?: boolean;
  strictSnapshots?: boolean;
  snapshotThresholdPercent?: number;
  timeoutMs?: number;
  viewports?: ViewportSpec[];
};

const DEFAULT_VIEWPORTS: ViewportSpec[] = [
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet", width: 768, height: 1024 },
  { name: "desktop", width: 1440, height: 900 },
];

function toFileUri(candidatePath: string): string {
  const resolved = path.resolve(candidatePath);
  return `file://${resolved}`;
}

function ensureHttpOrFileUrl(rawTarget: string): string {
  if (/^https?:\/\//i.test(rawTarget) || /^file:\/\//i.test(rawTarget)) {
    return rawTarget;
  }
  return toFileUri(rawTarget);
}

function dedupe(values: string[]): string[] {
  return [...new Set(values)];
}

async function runLayoutChecks(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const issues: string[] = [];

    const viewportWidth = window.innerWidth;
    const root = document.documentElement;

    if (root.scrollWidth > viewportWidth + 1) {
      issues.push(
        `Horizontal overflow detected (scrollWidth=${root.scrollWidth}, viewport=${viewportWidth}).`
      );
    }

    const outsideViewport = Array.from(document.querySelectorAll<HTMLElement>("body *"))
      .filter((element) => {
        const style = window.getComputedStyle(element);
        if (style.display === "none" || style.visibility === "hidden") {
          return false;
        }
        const rect = element.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) {
          return false;
        }
        return rect.left < -1 || rect.right > viewportWidth + 1;
      })
      .slice(0, 5)
      .map((element) => {
        const id = element.id ? `#${element.id}` : "";
        const cls = element.className ? `.${String(element.className).split(" ")[0]}` : "";
        return `${element.tagName.toLowerCase()}${id}${cls}`;
      });

    if (outsideViewport.length > 0) {
      issues.push(`Elements outside viewport bounds: ${outsideViewport.join(", ")}.`);
    }

    const clippingCandidates = Array.from(
      document.querySelectorAll<HTMLElement>("h1, h2, h3, p, span, label, button, th, td, a")
    )
      .filter((element) => {
        if (!element.textContent?.trim()) {
          return false;
        }
        return element.scrollWidth > element.clientWidth + 6;
      })
      .slice(0, 5)
      .map((element) => {
        const snippet = (element.textContent ?? "").trim().slice(0, 32);
        return `${element.tagName.toLowerCase()}('${snippet}')`;
      });

    if (clippingCandidates.length > 0) {
      issues.push(`Potential text clipping: ${clippingCandidates.join(", ")}.`);
    }

    return issues;
  });
}

async function runAxeChecks(page: Page): Promise<string[]> {
  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  return result.violations.map(
    (violation: { id: string; help: string; nodes: unknown[] }) =>
      `${violation.id}: ${violation.help} (${violation.nodes.length} nodes)`
  );
}

async function readPng(filePath: string): Promise<PNG> {
  const raw = await readFile(filePath);
  return PNG.sync.read(raw);
}

async function compareScreenshots(
  baselinePath: string,
  candidatePath: string
): Promise<{ diffPercent: number; detail?: string }> {
  const baseline = await readPng(baselinePath);
  const candidate = await readPng(candidatePath);

  if (baseline.width !== candidate.width || baseline.height !== candidate.height) {
    return {
      diffPercent: 100,
      detail: `Image dimensions differ (baseline=${baseline.width}x${baseline.height}, candidate=${candidate.width}x${candidate.height}).`,
    };
  }

  const diffPixels = pixelmatch(
    baseline.data,
    candidate.data,
    undefined,
    baseline.width,
    baseline.height,
    { threshold: 0.1 }
  );

  const diffPercent = Number(((diffPixels / (baseline.width * baseline.height)) * 100).toFixed(4));
  return { diffPercent };
}

export async function runPlaywrightVisualAudit(
  options: PlaywrightVisualAuditOptions
): Promise<PlaywrightVisualAuditResult> {
  const targetUrl = ensureHttpOrFileUrl(options.url);
  const timeoutMs = options.timeoutMs ?? 30_000;
  const snapshotThresholdPercent = options.snapshotThresholdPercent ?? 0.3;
  const strictSnapshots = options.strictSnapshots ?? true;
  const updateBaseline = options.updateBaseline ?? false;
  const viewports = options.viewports ?? DEFAULT_VIEWPORTS;

  await mkdir(options.screenshotDir, { recursive: true });
  const baselineRoot = path.resolve(options.snapshotDir, options.pageId);
  await mkdir(baselineRoot, { recursive: true });

  const browser = await chromium.launch({ headless: true });

  try {
    const viewportResults: ViewportAuditResult[] = [];
    const allA11yIssues: string[] = [];
    const allLayoutIssues: string[] = [];
    const snapshotDiffs: number[] = [];

    for (const viewport of viewports) {
      const context = await browser.newContext({
        viewport: { width: viewport.width, height: viewport.height },
      });

      const page = await context.newPage();
      await page.goto(targetUrl, { waitUntil: "networkidle", timeout: timeoutMs });

      const screenshotPath = path.resolve(
        options.screenshotDir,
        `${options.pageId}-${viewport.name}-${viewport.width}x${viewport.height}.png`
      );
      await page.screenshot({ path: screenshotPath, fullPage: true });

      const viewportIssues = await runLayoutChecks(page);
      const a11yIssues = await runAxeChecks(page);

      const baselinePath = path.resolve(
        baselineRoot,
        `${viewport.name}-${viewport.width}x${viewport.height}.png`
      );

      let snapshotDiffPercent: number | undefined;
      if (updateBaseline) {
        const imageBuffer = await readFile(screenshotPath);
        await writeFile(baselinePath, imageBuffer);
      } else {
        try {
          const diffResult = await compareScreenshots(baselinePath, screenshotPath);
          snapshotDiffPercent = diffResult.diffPercent;
          snapshotDiffs.push(snapshotDiffPercent);
          if (diffResult.detail) {
            viewportIssues.push(diffResult.detail);
          }
          if (snapshotDiffPercent > snapshotThresholdPercent) {
            viewportIssues.push(
              `Snapshot diff ${snapshotDiffPercent}% exceeds threshold ${snapshotThresholdPercent}%.`
            );
          }
        } catch {
          const missingBaseline = `Missing baseline snapshot for ${viewport.name} (${baselinePath}).`;
          if (strictSnapshots) {
            viewportIssues.push(missingBaseline);
          }
        }
      }

      allLayoutIssues.push(...viewportIssues.map((issue) => `[${viewport.name}] ${issue}`));
      allA11yIssues.push(...a11yIssues.map((issue) => `[${viewport.name}] ${issue}`));

      const issues = [...viewportIssues, ...a11yIssues];
      viewportResults.push({
        viewport: `${viewport.name}-${viewport.width}x${viewport.height}`,
        status: issues.length === 0 ? "passed" : "failed",
        issues,
        screenshotPath,
        snapshotDiffPercent,
      });

      await context.close();
    }

    return {
      viewportResults,
      a11yIssues: dedupe(allA11yIssues),
      layoutIssues: dedupe(allLayoutIssues),
      snapshotDiffPercent:
        snapshotDiffs.length > 0
          ? Number(Math.max(...snapshotDiffs).toFixed(4))
          : updateBaseline
            ? 0
            : undefined,
    };
  } finally {
    await browser.close();
  }
}
