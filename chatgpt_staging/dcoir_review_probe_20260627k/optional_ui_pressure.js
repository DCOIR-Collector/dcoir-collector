const childProcess = require("child_process");

export function renderPreview(input) {
  document.querySelector("#preview").innerHTML = input.html;
}

export function runNamedTool(name) {
  return childProcess.execSync(`tools/${name}`);
}
