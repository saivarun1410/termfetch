import { writeFile } from "node:fs/promises";
import webPush from "web-push";

const keys = webPush.generateVAPIDKeys();
const contents = [
  `VAPID_PUBLIC_KEY=${keys.publicKey}`,
  `VAPID_PRIVATE_KEY=${keys.privateKey}`,
  "VAPID_SUBJECT=mailto:saivarun1410@users.noreply.github.com",
  ""
].join("\n");

await writeFile(new URL("../.dev.vars", import.meta.url), contents, { mode: 0o600 });
process.stdout.write(`${keys.publicKey}\n`);
