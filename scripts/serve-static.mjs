import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { createServer } from "node:http";
import { dirname, extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import siteConfig from "../dashboard/site-config.cjs";

const { pagesBasePath } = siteConfig;

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const exportDirectory = join(projectRoot, "dashboard", "out");
const port = Number(process.env.PORT ?? "4173");
const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
};

function sendNotFound(response) {
  response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
  response.end("Not found");
}

function exportedPathFor(pathname) {
  if (!pathname.startsWith(`${pagesBasePath}/`)) {
    return null;
  }

  const relativePath = pathname.slice(pagesBasePath.length) || "/";
  const outputPath = resolve(exportDirectory, `.${relativePath}`);

  return outputPath === exportDirectory ||
    outputPath.startsWith(`${exportDirectory}/`)
    ? outputPath
    : null;
}

const server = createServer(async (request, response) => {
  const requestUrl = new URL(request.url ?? "/", "http://127.0.0.1");

  if (requestUrl.pathname === pagesBasePath) {
    response.writeHead(308, { location: `${pagesBasePath}/` });
    response.end();
    return;
  }

  let outputPath = exportedPathFor(requestUrl.pathname);
  if (outputPath === null) {
    sendNotFound(response);
    return;
  }

  try {
    if ((await stat(outputPath)).isDirectory()) {
      outputPath = join(outputPath, "index.html");
    }

    const file = await stat(outputPath);
    if (!file.isFile()) {
      sendNotFound(response);
      return;
    }
  } catch {
    sendNotFound(response);
    return;
  }

  response.writeHead(200, {
    "content-type":
      contentTypes[extname(outputPath)] ?? "application/octet-stream",
  });
  createReadStream(outputPath).pipe(response);
});

server.listen(port, "127.0.0.1");
