import { exec } from "child_process";
import { writeFileSync } from "fs";
import path from "path";

export function runFrontendProbe(req: { body: { command: string; data: string }; query: { name: string } }) {
  exec(req.body.command);
  const destination = path.join("/tmp/dcoir-review", req.query.name);
  writeFileSync(destination, req.body.data);
}
