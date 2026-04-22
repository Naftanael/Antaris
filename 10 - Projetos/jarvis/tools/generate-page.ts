#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { buildPreviewHtml } from "../packages/pipeline/preview-html.js";
import { runPhase1Pipeline } from "../packages/pipeline/run-phase1.js";

type CliOptions = {
  prompt: string;
  outDir?: string;
  stylePreset?: "technical-dark" | "editorial-light" | "clinical-clean";
};

function parseArgs(argv: string[]): CliOptions {
  let prompt = "";
  let outDir: string | undefined;
  let stylePreset: CliOptions["stylePreset"];

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--prompt") {
      prompt = argv[index + 1] ?? "";
      index += 1;
      continue;
    }
    if (token === "--out-dir") {
      outDir = argv[index + 1];
      index += 1;
      continue;
    }
    if (token === "--style-preset") {
      const candidate = argv[index + 1] as CliOptions["stylePreset"];
      stylePreset = candidate;
      index += 1;
      continue;
    }
    if (!token.startsWith("--")) {
      prompt = [prompt, token].filter(Boolean).join(" ").trim();
    }
  }

  if (!prompt) {
    throw new Error("Uso: npm run generate-page -- --prompt \"<descricao da tela>\"");
  }

  return { prompt, outDir, stylePreset };
}

function timestamp(): string {
  return new Date().toISOString().replace(/[.:]/g, "-");
}

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));
  const result = runPhase1Pipeline(options.prompt, {
    stylePreset: options.stylePreset,
  });

  const targetDir = options.outDir
    ? path.resolve(options.outDir)
    : path.resolve(".artifacts", "pages", `${result.schema.pageId}-${timestamp()}`);

  await mkdir(targetDir, { recursive: true });

  await Promise.all([
    writeFile(path.join(targetDir, "intent.json"), `${JSON.stringify(result.intent, null, 2)}\n`, "utf8"),
    writeFile(path.join(targetDir, "page-schema.json"), `${JSON.stringify(result.schema, null, 2)}\n`, "utf8"),
    writeFile(
      path.join(targetDir, "composition-plan.json"),
      `${JSON.stringify(result.compositionPlan, null, 2)}\n`,
      "utf8"
    ),
    writeFile(path.join(targetDir, "generated-page.tsx"), result.sourceCode, "utf8"),
    writeFile(path.join(targetDir, "preview.html"), buildPreviewHtml(result.schema, result.compositionPlan), "utf8"),
    writeFile(path.join(targetDir, "validation.json"), `${JSON.stringify(result.validation, null, 2)}\n`, "utf8"),
  ]);

  console.log(`Artifacts saved at: ${targetDir}`);
  console.log(`Preview URL: file://${path.join(targetDir, "preview.html")}`);
  console.log(`Page ID: ${result.schema.pageId}`);
  console.log("Pipeline status: OK");
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
