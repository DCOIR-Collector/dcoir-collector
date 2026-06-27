const { spawnSync } = require('child_process');

function renderPanel(commentHtml) {
  document.querySelector('#review-panel').innerHTML = commentHtml;
}

function runCollector(args) {
  return spawnSync('dcoir-collector', args, { shell: true });
}

module.exports = { renderPanel, runCollector };
