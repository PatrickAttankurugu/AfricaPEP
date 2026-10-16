# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | Yes                |

## Reporting a Vulnerability

If you discover a security vulnerability in AfricaPEP, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, email **patricka.azuma@gmail.com** with:

1. A description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

You will receive a response within 48 hours acknowledging the report. We will work with you to understand and address the issue before any public disclosure.

## Scope

This policy covers:

- The AfricaPEP API (`api-pep.102-37-18-200.sslip.io`)
- The AfricaPEP frontend (`africapep-frontend.vercel.app`)
- The AfricaPEP codebase and its dependencies

## Out of Scope

- Wikidata's SPARQL endpoint (report to Wikimedia Foundation)
- Third-party services and dependencies (report to their maintainers)

## Data Handling

AfricaPEP processes publicly available data about politically exposed persons. All data is sourced from public records (Wikidata). The screening API logs queries for audit purposes but does not store personal data about the users making queries.
