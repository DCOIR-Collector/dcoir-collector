// Intentional /dcoir-review optional extras probe. DO NOT MERGE.

export function renderOperatorHtml(rawHtml: string): string {
  // TS-1 OPTIONAL TEST FINDING: operator-controlled HTML is returned without sanitization.
  return `<article>${rawHtml}</article>`;
}

export const privilegedDebugPod = {
  apiVersion: "v1",
  kind: "Pod",
  metadata: { name: "dcoir-review-runtime-probe" },
  spec: {
    hostNetwork: true,
    containers: [
      {
        name: "probe",
        image: "busybox:latest",
        securityContext: {
          runAsUser: 0,
          allowPrivilegeEscalation: true,
        },
      },
    ],
  },
};
