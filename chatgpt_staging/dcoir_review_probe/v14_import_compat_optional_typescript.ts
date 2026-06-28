export function renderProfile(target: HTMLElement, profile: { bio: string; script: string }) {
  target.innerHTML = profile.bio;
  setTimeout(profile.script, 1000);
}
