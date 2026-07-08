# Security Policy

## Supported versions

Only the latest release receives security fixes.

| Version | Supported |
| ------- | --------- |
| latest  | ✅        |
| older   | ❌        |

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Instead, use GitHub's
private vulnerability reporting:

**[Report a vulnerability](https://github.com/Safronus/BLURAnything/security/advisories/new)**

You can expect an initial response within 7 days. Once a fix is released, the report
will be credited in the release notes (unless you prefer otherwise).

## Scope notes

- BLURAnything processes local image files and screenshots; it makes no network requests.
- Gaussian blur is not a cryptographically safe redaction method for text — heavily
  blurred text can sometimes be partially reconstructed. Irreversible modes (pixelate,
  solid fill) are tracked on the issue tracker.
