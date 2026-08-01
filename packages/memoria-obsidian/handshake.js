// Pure handshake-client logic: argv construction, stdout parsing, spawn-error
// classification, and the bounded-respawn gate (bootstrap spec sections 2-3).
// No Obsidian imports; headless-testable with node.

const HANDSHAKE_TIMEOUT_MS = 10000;
const RESPAWN_LIMIT = 3;
const RESPAWN_WINDOW_MS = 3 * 60 * 1000;

function buildHandshakeArgv(engineCommand, vaultPath) {
  const parts = String(engineCommand || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length === 0) {
    parts.push("memoria");
  }
  return {
    command: parts[0],
    args: [...parts.slice(1), "handshake", "--vault", String(vaultPath), "--spawn", "--json"],
  };
}

function parseHandshake(stdoutText) {
  let payload;
  try {
    payload = JSON.parse(String(stdoutText || ""));
  } catch {
    throw new Error("handshake: stdout is not JSON");
  }
  const coordinates = {
    port: Number(payload.port),
    token: String(payload.token || ""),
    bootId: String(payload.boot_id || ""),
    engineVersion: String(payload.engine_version || ""),
    pid: Number(payload.pid || 0),
  };
  if (!Number.isInteger(coordinates.port) || coordinates.port <= 0) {
    throw new Error("handshake: missing port");
  }
  if (!coordinates.token) {
    throw new Error("handshake: missing token");
  }
  if (!coordinates.bootId) {
    throw new Error("handshake: missing boot_id");
  }
  if (!coordinates.engineVersion) {
    throw new Error("handshake: missing engine_version");
  }
  if (!Number.isInteger(coordinates.pid) || coordinates.pid <= 0) {
    throw new Error("handshake: missing pid");
  }
  return coordinates;
}

function classifySpawnError(error) {
  return error && error.code === "ENOENT" ? "engine-missing" : "spawn-failed";
}

function createRespawnGate(now = Date.now) {
  const attempts = [];
  const prune = () => {
    const cutoff = now() - RESPAWN_WINDOW_MS;
    while (attempts.length && attempts[0] <= cutoff) {
      attempts.shift();
    }
  };
  return {
    tryAcquire() {
      prune();
      if (attempts.length >= RESPAWN_LIMIT) {
        return false;
      }
      attempts.push(now());
      return true;
    },
    exhausted() {
      prune();
      return attempts.length >= RESPAWN_LIMIT;
    },
  };
}

module.exports = {
  HANDSHAKE_TIMEOUT_MS,
  RESPAWN_LIMIT,
  RESPAWN_WINDOW_MS,
  buildHandshakeArgv,
  classifySpawnError,
  createRespawnGate,
  parseHandshake,
};
