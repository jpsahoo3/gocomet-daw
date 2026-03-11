/**
 * Browser-side logger.
 * Forwards errors (and optionally warnings) to the backend POST /v1/log
 * so they land in logs/frontend.log with daily rotation.
 *
 * Usage:
 *   import logger from "./services/logger";
 *   logger.error("Payment failed", { context: "PaymentPanel", stack: err.stack });
 */

const BASE = "http://localhost:8000";

async function send(level, message, { context, stack } = {}) {
  try {
    await fetch(`${BASE}/v1/log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level, message, context, stack }),
    });
  } catch {
    // Silently ignore — if the backend is down, we can't log anyway
  }
}

const logger = {
  debug:    (msg, opts) => send("debug",    msg, opts ?? {}),
  info:     (msg, opts) => send("info",     msg, opts ?? {}),
  warn:     (msg, opts) => send("warning",  msg, opts ?? {}),
  error:    (msg, opts) => send("error",    msg, opts ?? {}),
  critical: (msg, opts) => send("critical", msg, opts ?? {}),
};

// Capture unhandled JS errors automatically
if (typeof window !== "undefined") {
  window.addEventListener("error", (event) => {
    logger.error(event.message, {
      context: "window.onerror",
      stack: event.error?.stack,
    });
  });

  window.addEventListener("unhandledrejection", (event) => {
    const msg =
      event.reason instanceof Error
        ? event.reason.message
        : String(event.reason);
    logger.error(`Unhandled promise rejection: ${msg}`, {
      context: "unhandledrejection",
      stack: event.reason?.stack,
    });
  });
}

export default logger;
