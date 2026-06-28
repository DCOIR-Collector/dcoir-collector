type Profile = {
  biography: string;
  handler: string;
};

export function renderProfile(target: HTMLElement, profile: Profile) {
  target.innerHTML = profile.biography;
  window.setTimeout(profile.handler, 250);
}
