import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createLogger } from './logger.js';

// The logger tags every line with its source and gates debug/info behind
// import.meta.env.DEV, while warn/error always fire. DEV is stubbed per test so
// the gating is asserted in both dev and production builds.
describe('createLogger', () => {
  let spies;

  beforeEach(() => {
    spies = {
      debug: vi.spyOn(console, 'debug').mockImplementation(() => {}),
      info: vi.spyOn(console, 'info').mockImplementation(() => {}),
      warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
      error: vi.spyOn(console, 'error').mockImplementation(() => {}),
    };
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it('prefixes every line with the source tag and forwards all args', () => {
    vi.stubEnv('DEV', true);
    const log = createLogger('deck');
    log.warn('boom', 42, { x: 1 });
    expect(spies.warn).toHaveBeenCalledWith('[deck]', 'boom', 42, { x: 1 });
  });

  it('emits debug and info in a dev build', () => {
    vi.stubEnv('DEV', true);
    const log = createLogger('app');
    log.debug('d');
    log.info('i');
    expect(spies.debug).toHaveBeenCalledWith('[app]', 'd');
    expect(spies.info).toHaveBeenCalledWith('[app]', 'i');
  });

  it('silences debug and info outside a dev build', () => {
    vi.stubEnv('DEV', false);
    const log = createLogger('app');
    log.debug('d');
    log.info('i');
    expect(spies.debug).not.toHaveBeenCalled();
    expect(spies.info).not.toHaveBeenCalled();
  });

  it('always emits warn and error, even in a production build', () => {
    vi.stubEnv('DEV', false);
    const log = createLogger('app');
    log.warn('w');
    log.error('e');
    expect(spies.warn).toHaveBeenCalledWith('[app]', 'w');
    expect(spies.error).toHaveBeenCalledWith('[app]', 'e');
  });
});
