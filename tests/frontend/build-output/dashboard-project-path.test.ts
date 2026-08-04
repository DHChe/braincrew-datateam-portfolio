import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { pagesBasePath } from "../../../dashboard/site-config.cjs";

const exportDirectory = fileURLToPath(
  new URL("../../../dashboard/out/", import.meta.url),
);
const entryPagePath = join(exportDirectory, "index.html");

async function readExportedEntryPage() {
  try {
    return await readFile(entryPagePath, "utf8");
  } catch (error: unknown) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      throw new Error(
        `${entryPagePath} not found — run "npm run build" first`,
        { cause: error },
      );
    }

    throw error;
  }
}

describe("dashboard project-path export", () => {
  it("prefixes entry-page static resources and emits them at that mounted path", async () => {
    const entryPage = await readExportedEntryPage();
    const staticResourcePaths = Array.from(
      entryPage.matchAll(/(?:href|src)="([^"]*\/_next\/[^\"]+)"/g),
      ([, resourcePath]) => resourcePath,
    );

    expect(staticResourcePaths).not.toHaveLength(0);

    for (const resourcePath of staticResourcePaths) {
      const pathname = new URL(resourcePath, "https://example.test").pathname;

      expect(pathname).toMatch(new RegExp(`^${pagesBasePath}/_next/`));
      expect(
        existsSync(join(exportDirectory, pathname.slice(pagesBasePath.length))),
      ).toBe(true);
    }
  });
});
