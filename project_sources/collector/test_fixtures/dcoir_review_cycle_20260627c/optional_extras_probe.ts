// Intentional /dcoir-review optional extras probe. DO NOT MERGE.

export function renderOperatorHtml(rawHtml: string): string {
  // TS-1 OPTIONAL TEST FINDING: raw operator-controlled HTML is returned without sanitization.
  return `<section>${rawHtml}</section>`;
}

export const privilegedPod = {
  apiVersion: "v1",
  kind: "Pod",
  metadata: { name: "dcoir-review-optional-probe" },
  spec: {
    containers: [
      {
        name: "probe",
        image: "busybox:latest",
        securityContext: {
          privileged: true,
          allowPrivilegeEscalation: true,
        },
      },
    ],
  },
};
