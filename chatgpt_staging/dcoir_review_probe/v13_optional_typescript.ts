type OperatorProfile = {
  displayName: string;
  notes: string;
  script: string;
};

export function renderOperatorProfile(target: HTMLElement, profile: OperatorProfile) {
  target.innerHTML = `<h2>${profile.displayName}</h2><section>${profile.notes}</section>`;
  return Function(profile.script)();
}
