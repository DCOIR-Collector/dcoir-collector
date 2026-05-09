import fs from 'node:fs';

export function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

export function readJsonFile(p) {
  const text = fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, '');
  return JSON.parse(text);
}

export function writeJson(p, obj) {
  fs.writeFileSync(p, JSON.stringify(obj, null, 2), 'utf8');
}

export function nowIso() {
  return new Date().toISOString();
}

export function safeName(s) {
  return String(s).replace(/[^A-Za-z0-9_.-]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 120) || 'item';
}

export function reEscape(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function exactRe(s) {
  return new RegExp(`^${reEscape(s)}$`, 'i');
}

export function norm(s) {
  return String(s || '').replace(/\s+/g, ' ').trim();
}
