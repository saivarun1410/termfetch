import { randomBytes } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";

const accessKey = `tf_${randomBytes(24).toString("base64url")}`;
const sessionSecret = randomBytes(32).toString("base64url");
const contents = [
  `APP_ACCESS_KEY=${accessKey}`,
  `SESSION_SECRET=${sessionSecret}`,
  ""
].join("\n");

await writeFile(new URL("../.access.vars", import.meta.url), contents, { mode: 0o600 });
const developmentFile = new URL("../.dev.vars", import.meta.url);
const developmentVars = await readFile(developmentFile, "utf8").catch(() => "");
const preserved = developmentVars
  .split("\n")
  .filter(
    (line) =>
      line && !line.startsWith("APP_ACCESS_KEY=") && !line.startsWith("SESSION_SECRET=")
  );
await writeFile(developmentFile, `${preserved.join("\n")}\n${contents}`, { mode: 0o600 });
process.stdout.write(`${accessKey}\n`);
