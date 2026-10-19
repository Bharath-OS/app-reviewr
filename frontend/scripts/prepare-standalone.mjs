import { cpSync, existsSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const standalone = join(root, ".next", "standalone");
const serverJs = join(standalone, "server.js");
const standaloneNext = join(standalone, ".next");

if (!existsSync(serverJs)) {
  console.error(
    "Missing .next/standalone/server.js — run `next build` first (or `npm run build`).",
  );
  process.exit(1);
}

mkdirSync(standaloneNext, { recursive: true });
cpSync(join(root, "public"), join(standalone, "public"), { recursive: true });
cpSync(join(root, ".next", "static"), join(standaloneNext, "static"), {
  recursive: true,
});
console.log("Standalone assets ready.");
