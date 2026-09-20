import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { resolve, relative, sep } from "node:path";

const [packageRootArg, manifestArg] = process.argv.slice(2);
if (!packageRootArg) {
  console.error("usage: node verify-release-package.mjs <package-root> [manifest-json]");
  process.exit(2);
}

const packageRoot = resolve(packageRootArg);
const manifestPath = resolve(manifestArg ?? new URL("./mission-003.acceptance.json", import.meta.url).pathname);
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));

const missing = [];
for (const path of manifest.required_files ?? []) {
  if (!existsSync(resolve(packageRoot, path))) missing.push(path);
}

const forbiddenHits = [];
const forbidden = (manifest.forbidden_path_fragments ?? []).map((value) => String(value).toLowerCase());

function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = resolve(dir, entry.name);
    const rel = relative(packageRoot, full).split(sep).join("/");
    const relLower = rel.toLowerCase();
    if (forbidden.some((needle) => relLower.includes(needle))) {
      forbiddenHits.push(rel);
      if (entry.isDirectory()) continue;
    }
    if (entry.isDirectory()) walk(full);
  }
}

if (!existsSync(packageRoot) || !statSync(packageRoot).isDirectory()) {
  console.error(`package root is not a directory: ${packageRoot}`);
  process.exit(2);
}

walk(packageRoot);

const result = {
  contract_id: manifest.contract_id,
  package_root: packageRoot,
  required_count: (manifest.required_files ?? []).length,
  missing_count: missing.length,
  missing,
  forbidden_count: forbiddenHits.length,
  forbidden_hits: forbiddenHits,
  pass: missing.length === 0 && forbiddenHits.length === 0
};

console.log(JSON.stringify(result, null, 2));
process.exit(result.pass ? 0 : 1);
