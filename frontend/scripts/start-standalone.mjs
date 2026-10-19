import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";

const serverJs = join(process.cwd(), ".next", "standalone", "server.js");

if (!existsSync(serverJs)) {
  console.error(
    "Missing .next/standalone/server.js — run `npm run build` first.",
  );
  process.exit(1);
}

const child = spawn(process.execPath, [serverJs], {
  stdio: "inherit",
  env: {
    ...process.env,
    PORT: process.env.PORT || "3741",
    HOSTNAME: process.env.HOSTNAME || "0.0.0.0",
  },
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});
