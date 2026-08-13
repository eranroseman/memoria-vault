import { build } from "esbuild";
import { mkdir, readdir, readFile, unlink, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { format } from "oxfmt";

const args = process.argv.slice(2);
if (args.length > 1 || (args.length === 1 && args[0] !== "--check")) {
  throw new Error("usage: node scripts/build.mjs [--check]");
}

const packageDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const formatterOptions = JSON.parse(
  await readFile(resolve(packageDir, "../../.oxfmtrc.json"), "utf8"),
);
delete formatterOptions.$schema;
delete formatterOptions.ignorePatterns;

async function formatArtifact(name, contents) {
  const result = await format(name, Buffer.from(contents).toString("utf8"), formatterOptions);
  if (result.errors.length) {
    throw new Error(
      `Oxfmt could not format ${name}:\n${result.errors.map(({ message }) => message).join("\n")}`,
    );
  }
  return Buffer.from(result.code);
}

const sourceDir = resolve(packageDir, "src");
const seedDir = resolve(
  packageDir,
  "../../src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian",
);
const bundled = await build({
  entryPoints: [resolve(sourceDir, "main.js")],
  outfile: resolve(seedDir, "main.js"),
  bundle: true,
  format: "cjs",
  platform: "node",
  external: ["obsidian"],
  write: false,
  logLevel: "silent",
});

const expected = new Map([
  ["main.js", await formatArtifact("main.js", bundled.outputFiles[0].contents)],
  ["manifest.json", await readFile(resolve(packageDir, "manifest.json"))],
  [
    "styles.css",
    await formatArtifact("styles.css", await readFile(resolve(packageDir, "styles.css"))),
  ],
]);

async function seedEntries() {
  try {
    return await readdir(seedDir);
  } catch (error) {
    if (error && error.code === "ENOENT") return [];
    throw error;
  }
}

if (args[0] === "--check") {
  const actual = new Set(await seedEntries());
  const problems = [];
  for (const [name, bytes] of expected) {
    try {
      const current = await readFile(resolve(seedDir, name));
      if (!current.equals(bytes)) problems.push(`${name}: byte-different`);
    } catch (error) {
      if (error && error.code === "ENOENT") problems.push(`${name}: missing`);
      else throw error;
    }
  }
  for (const name of actual) {
    if (!expected.has(name)) problems.push(`${name}: unexpected`);
  }
  if (problems.length) throw new Error(`stale Obsidian plugin artifact:\n${problems.join("\n")}`);
} else {
  await mkdir(seedDir, { recursive: true });
  for (const [name, bytes] of expected) await writeFile(resolve(seedDir, name), bytes);
  for (const name of await seedEntries()) {
    if (!expected.has(name)) await unlink(resolve(seedDir, name));
  }
}
