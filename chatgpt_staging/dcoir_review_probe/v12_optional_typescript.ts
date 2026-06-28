type Profile = {
  displayName: string;
  biography: string;
};

export function renderProfile(target: HTMLElement, profile: Profile) {
  target.innerHTML = `<h2>${profile.displayName}</h2><p>${profile.biography}</p>`;
}
