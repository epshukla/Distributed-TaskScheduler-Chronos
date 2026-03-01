# Security Policy

## Supported Versions

Chronos-K8s-Scheduler is currently in early development (`0.1.x`). Security fixes are applied to the latest version only.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Known Security Considerations

- **Docker socket mounting** — Workers mount [/var/run/docker.sock](cci:7://file:///var/run/docker.sock:0:0-0:0), which grants container-level host access. In production, use Docker-in-Docker (DinD), rootless Docker, or a dedicated container runtime per worker node.
- **etcd / Redis** — Ensure TLS is enabled and access is restricted in production deployments. The default Docker Compose configuration uses unauthenticated connections suitable only for local development.
- **API authentication** — The current API does not enforce authentication or authorization. Do not expose it to untrusted networks without adding an auth layer.

## Reporting a Vulnerability

If you discover a security vulnerability in Chronos-K8s-Scheduler, please report it responsibly:

1. **Email**: Send a detailed description to **eshanshukla00.com** (replace with your actual contact).
2. **Do NOT** open a public GitHub issue for security vulnerabilities.
3. Include:
   - A description of the vulnerability and its potential impact.
   - Steps to reproduce.
   - Affected version(s).
   - Any suggested fix (optional).

### What to Expect

- **Acknowledgment** within **48 hours** of your report.
- **Status update** within **7 days** with an assessment and remediation timeline.
- If accepted, a fix will be released as soon as possible and you will be credited (unless you prefer anonymity).
- If declined, we will explain why the report does not qualify.

We appreciate responsible disclosure and will not take legal action against researchers who report vulnerabilities in good faith.
