/**
 * Backend API base URL (FastAPI; SOTA port 10750).
 * Override with NEXT_PUBLIC_API_URL.
 */
export const API_BASE =
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) ||
  'http://localhost:10750'
