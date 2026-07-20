// Tiny logging helper so log calls read consistently across the app.
//
// `debug` and `info` are silenced outside dev (import.meta.env.DEV is false in
// production builds) to keep the shipped console quiet; `warn` and `error`
// always fire so real problems surface wherever the app runs. Each line is
// prefixed with the source tag passed to `createLogger` (e.g. "[deck]") so it's
// clear where a message came from.

function makeLogger(level, tag, devOnly) {
  return (...args) => {
    if (devOnly && !import.meta.env.DEV) return;
    // eslint-disable-next-line no-console
    console[level](`[${tag}]`, ...args);
  };
}

export function createLogger(tag) {
  return {
    debug: makeLogger('debug', tag, true),
    info: makeLogger('info', tag, true),
    warn: makeLogger('warn', tag, false),
    error: makeLogger('error', tag, false),
  };
}
