import fs from "node:fs";
import path from "node:path";
import type { Request, Response } from "express";

export function writeReport(req: Request, res: Response) {
  const destination = path.join("/tmp/dcoir", String(req.query.name ?? "report.txt"));
  fs.writeFileSync(destination, String(req.body ?? ""));
  res.send("ok");
}
