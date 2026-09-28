# Security policy

Blender-CamSight is a local Blender add-on. It does not run a network service and it does not collect account data.

## Supported versions

| Version | Status |
| --- | --- |
| 1.0.x on `develop` | Supported |
| Older tags, if any | Unsupported |

Security fixes target Blender 4.2 and newer.

## What to report

Report a vulnerability if the add-on can be used to:

- execute unexpected code when a `.blend` file is opened
- read or write files outside the behavior a Blender add-on normally has
- keep running, or keep a handler installed, after the add-on is disabled

Crashes in the viewport draw path, incorrect framing, and performance problems belong in a normal bug report. See [SUPPORT.md](SUPPORT.md).

## How to report

Use GitHub Security Advisories for this repository: **Security → Report a vulnerability**.

Do not open a public issue for an unfixed vulnerability. Include the Blender version, operating system, and a minimal `.blend` file or steps. You will receive a reply after the maintainers confirm the report.

## Disclosure

Please give the maintainers time to ship a fix before writing about the problem in public. A fixed release will be noted in [CHANGELOG.md](CHANGELOG.md).
