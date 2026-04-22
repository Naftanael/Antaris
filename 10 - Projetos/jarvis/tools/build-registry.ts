#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { componentRegistry } from "../packages/design-system/registry/components.js";

async function main(): Promise<void> {
  const outDir = path.resolve(".artifacts", "registry");
  const outPath = path.join(outDir, "component-registry.json");

  await mkdir(outDir, { recursive: true });
  await writeFile(outPath, `${JSON.stringify(componentRegistry, null, 2)}\n`, "utf8");

  console.log(`Registry exported to: ${outPath}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
