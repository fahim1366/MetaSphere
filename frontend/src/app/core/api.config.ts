/**
 * Same-origin API locations.
 *
 * In production nginx proxies /api and /health to the backend; in development
 * `ng serve` does the same through proxy.conf.json. No absolute host is ever hard-coded,
 * which keeps the build portable for on-premises / air-gapped deployments.
 */
export const API_BASE = "/api/v1";
export const HEALTH_BASE = "/health";
