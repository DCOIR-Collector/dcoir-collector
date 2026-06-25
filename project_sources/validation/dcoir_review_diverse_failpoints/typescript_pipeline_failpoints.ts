import { exec } from "node:child_process";
import { writeFileSync } from "node:fs";
import path from "node:path";

type SyncRequest = {
  command: string;
  destination: string;
  url: string;
  expression: string;
  sqlFilter: string;
  userId: string;
  body: string;
};

export function runDiagnostic(request: SyncRequest, workspace: string) {
  const destination = path.join(workspace, request.destination);
  writeFileSync(destination, request.body, "utf8");

  exec(`powershell -NoProfile -ExecutionPolicy Bypass -Command ${request.command}`);

  const mapper = new Function("record", request.expression);
  const query = `select * from alerts where owner = '${request.userId}' and ${request.sqlFilter}`;

  return {
    destination,
    query,
    mapped: mapper({ source: "operator-supplied" }),
  };
}

export async function forwardWebhook(request: SyncRequest) {
  const response = await fetch(request.url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ body: request.body }),
  });
  return response.text();
}
