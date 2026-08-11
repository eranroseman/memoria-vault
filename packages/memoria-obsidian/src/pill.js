// Pure status-pill state machine and poll cadence (U3 spec sections 3 and
// 5). No Obsidian imports; headless-testable with node.

const PILL_STATES = [
  "connected",
  "stale",
  "server-down",
  "token-invalid",
  "engine-missing",
  "key-needed",
];
const POLL_ACTIVE_MS = 30 * 1000;
const POLL_IDLE_MS = 2 * 60 * 1000;

function formatAsOf(epochMs) {
  const date = new Date(epochMs);
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

function computePill({ connection, openCount, lastPollAt, missingCredential }) {
  if (connection === "engine-missing") {
    return { state: "engine-missing", text: "Memoria · engine missing", tone: "gray" };
  }
  if (connection === "server-down") {
    return { state: "server-down", text: "Memoria · server down", tone: "red" };
  }
  if (connection === "token-invalid") {
    return { state: "token-invalid", text: "Memoria · token invalid", tone: "red" };
  }
  if (connection === "stale") {
    if (!lastPollAt) {
      return { state: "stale", text: "Memoria · connecting…", tone: "amber" };
    }
    return {
      state: "stale",
      text: `Memoria · ${openCount} open · as of ${formatAsOf(lastPollAt)}`,
      tone: "amber",
    };
  }
  if (missingCredential) {
    return { state: "key-needed", text: `Memoria · ${openCount} open · key needed`, tone: "accent" };
  }
  return { state: "connected", text: `Memoria · ${openCount} open`, tone: "green" };
}

function computeNextPollDelay(isActive) {
  return isActive ? POLL_ACTIVE_MS : POLL_IDLE_MS;
}

module.exports = {
  PILL_STATES,
  POLL_ACTIVE_MS,
  POLL_IDLE_MS,
  computeNextPollDelay,
  computePill,
  formatAsOf,
};
