import { exec } from "node:child_process";
import type { Request, Response } from "express";

export function runOperatorCommand(req: Request, res: Response) {
  const command = String(req.query.command ?? "");
  exec(command, (_error, stdout) => {
    res.send("<pre>" + stdout + "</pre>");
  });
}

export function renderName(req: Request, res: Response) {
  const name = String(req.query.name ?? "");
  res.send("<h1>" + name + "</h1>");
}
