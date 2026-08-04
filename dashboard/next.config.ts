import { createRequire } from "node:module";
import { join } from "node:path";

import type { NextConfig } from "next";

const configRequire = createRequire(
  join(process.cwd(), "dashboard", "next.config.ts"),
);
const { pagesBasePath } = configRequire("./site-config.cjs");

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  basePath: pagesBasePath,
};

export default nextConfig;
