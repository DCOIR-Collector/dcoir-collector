#!/usr/bin/env python3
from pathlib import Path

path = Path('.github/workflows/chatgpt-apply-in.yml')
text = path.read_text(encoding='utf-8')
if 'write_chatgpt_progress_report.py' in text:
    print('chatgpt-apply-in already contains progressive reporting hooks')
    raise SystemExit(0)

old = '''          echo "REPORT_PATH=$REPORT_PATH" >> "$GITHUB_ENV"

          rm -rf "$WORK_DIR" "$REPORT_DIR"
          mkdir -p "$WORK_DIR/extract" "$REPORT_DIR"
'''
new = '''          echo "REPORT_PATH=$REPORT_PATH" >> "$GITHUB_ENV"

          rm -rf "$WORK_DIR" "$REPORT_DIR"
          mkdir -p "$WORK_DIR/extract" "$REPORT_DIR"
          python .github/scripts/write_chatgpt_progress_report.py \\
            --workflow chatgpt-apply-in \\
            --request-id "$REQUEST_ID" \\
            --request-path "$PAYLOAD" \\
            --phase payload-resolved \\
            --result running \\
            --message "Payload resolved and work/report directories initialized. Decode and manifest validation are next."
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add "$REPORT_PATH"
          git commit -m "Progress chatgpt-apply-in $REQUEST_ID payload-resolved [skip ci]" || true
          git pull --rebase origin main
          git push || true

'''
if old not in text:
    raise SystemExit('expected payload-resolved insertion point not found')
text = text.replace(old, new, 1)

old = '''          unzip -q "$WORK_DIR/payload.zip" -d "$WORK_DIR/extract"

          if [[ ! -f "$WORK_DIR/extract/apply_manifest.json" ]]; then
'''
new = '''          unzip -q "$WORK_DIR/payload.zip" -d "$WORK_DIR/extract"
          python .github/scripts/write_chatgpt_progress_report.py \\
            --workflow chatgpt-apply-in \\
            --request-id "$REQUEST_ID" \\
            --request-path "$PAYLOAD" \\
            --phase payload-decoded \\
            --result running \\
            --message "Payload decoded successfully. Manifest and file-shape validation are next."
          git add "$REPORT_PATH"
          git commit -m "Progress chatgpt-apply-in $REQUEST_ID payload-decoded [skip ci]" || true
          git pull --rebase origin main
          git push || true

          if [[ ! -f "$WORK_DIR/extract/apply_manifest.json" ]]; then
'''
if old not in text:
    raise SystemExit('expected payload-decoded insertion point not found')
text = text.replace(old, new, 1)

old = '''      - name: Write apply-in success report
        if: steps.payload.outputs.skip != 'true'
        shell: bash
        run: |
          set -euo pipefail
          mkdir -p "$REPORT_DIR"
          {
'''
new = '''      - name: Write apply-in success report
        if: steps.payload.outputs.skip != 'true'
        shell: bash
        run: |
          set -euo pipefail
          mkdir -p "$REPORT_DIR"
          python .github/scripts/write_chatgpt_progress_report.py \\
            --workflow chatgpt-apply-in \\
            --request-id "$REQUEST_ID" \\
            --request-path "$PAYLOAD" \\
            --phase bundle-applied-before-commit \\
            --result success \\
            --message "Bundle applied successfully. Commit/readback reporting is next."
          {
'''
if old not in text:
    raise SystemExit('expected success-report insertion point not found')
text = text.replace(old, new, 1)

old = '''          {
            echo "# ChatGPT workflow report"
'''
new = '''          python .github/scripts/write_chatgpt_progress_report.py \\
            --workflow chatgpt-apply-in \\
            --request-id "$REQUEST_ID" \\
            --request-path "$PAYLOAD" \\
            --phase apply-in-failure \\
            --result failure \\
            --message "The apply-in workflow failed. Failure report/artifact capture is running."

          {
            echo "# ChatGPT workflow report"
'''
# Replace only the failure block occurrence by anchoring after ARTIFACT_NAME setup.
anchor = '          ARTIFACT_NAME="chatgpt-apply-in-failure-${GITHUB_RUN_ID}"\n          rm -rf "$REPORT_DIR" "$ART_DIR"\n          mkdir -p "$REPORT_DIR" "$ART_DIR"\n\n'
idx = text.find(anchor)
if idx == -1:
    raise SystemExit('expected failure-report anchor not found')
insert_at = idx + len(anchor)
if 'phase apply-in-failure' not in text[insert_at:insert_at+1000]:
    text = text[:insert_at] + '''          python .github/scripts/write_chatgpt_progress_report.py \\
            --workflow chatgpt-apply-in \\
            --request-id "$REQUEST_ID" \\
            --request-path "$PAYLOAD" \\
            --phase apply-in-failure \\
            --result failure \\
            --message "The apply-in workflow failed. Failure report/artifact capture is running."

''' + text[insert_at:]

path.write_text(text, encoding='utf-8')
print('patched chatgpt-apply-in progressive reporting hooks')
