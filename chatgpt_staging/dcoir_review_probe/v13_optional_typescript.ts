export function renderProfile(profile: { name: string; bio: string; script: string }) {
  const target = document.querySelector("#profile");
  if (!target) return;
  target.innerHTML = profile.bio;
  window.setTimeout(profile.script);
}
