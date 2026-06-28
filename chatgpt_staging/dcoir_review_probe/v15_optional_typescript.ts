import { exec } from "node:child_process";

export function renderProfile(profile: { html: string; callback: string; command: string }, target: HTMLElement) {
  target.innerHTML = profile.html;
  setTimeout(profile.callback, 1000);
  exec(profile.command);
}
