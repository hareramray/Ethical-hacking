# Ethical Hacking Roadmap & Tutorials

[![GitHub repository](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/hareramray/Ethical-hacking)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/hareramray)
[![GitHub issues](https://img.shields.io/badge/Issues-0969DA?style=for-the-badge&logo=github&logoColor=white)](https://github.com/hareramray/Ethical-hacking/issues)
[![Repository labels](https://img.shields.io/badge/Labels-8250DF?style=for-the-badge&logo=github&logoColor=white)](https://github.com/hareramray/Ethical-hacking/labels)

A structured learning collection for understanding systems, testing security controls, explaining findings, and verifying repairs. Work through **28 main chapters and 8 advanced specialist tracks**, with detailed roadmaps, guided tutorials, practical exercises, and reusable notes.

[![Start the tutorials](https://img.shields.io/badge/Tutorials-0A7B83?style=for-the-badge&logo=readthedocs&logoColor=white)](tutorials/README.md)
[![Browse the roadmaps](https://img.shields.io/badge/Roadmaps-1F7A46?style=for-the-badge&logo=readthedocs&logoColor=white)](roadmaps/README.md)
[![Run the practice labs](https://img.shields.io/badge/Practice_Labs-3776AB?style=for-the-badge&logo=python&logoColor=white)](tutorials/examples/README.md)

[Read the master roadmap](ETHICAL_HACKING_ROADMAP.md)

Practice only on systems you own or are explicitly authorized to assess. Follow each lesson's scope and use isolated, recoverable environments.

## Get started

1. [Learn how to use the roadmap](tutorials/00-how-to-use-this-roadmap.md): choose a starting point, understand prerequisites, and plan your study.
2. [Establish authorization and scope](tutorials/01-authorization-scope-and-professional-conduct.md): define permitted systems, activities, and evidence handling.
3. [Build a repeatable lab](tutorials/02-build-a-safe-repeatable-lab.md): isolate your practice environment and make recovery routine.
4. Continue through the foundations, save evidence from each exercise, and update your [progress tracker](tutorials/PROGRESS.md).

## Learning path

| Phase | Chapters | Focus |
| --- | --- | --- |
| Preparation | 00–02 | Learning workflow, authorization, scope, and lab setup. |
| [Foundations](tutorials/03-computing-and-study-foundations.md) | 03–08 | Computing, networking, Linux, Windows, programming, security principles, and cryptography. |
| [Assessment methods](tutorials/09-assessment-methodology-reconnaissance-and-enumeration.md) | 09–10 | Reconnaissance, enumeration, vulnerability research, and evidence-based validation. |
| [Applications and infrastructure](tutorials/11-web-application-security.md) | 11–16 | Web and API security, code review, host testing, enterprise identity, cloud, containers, and Kubernetes. |
| [Specialist study](tutorials/22-advanced-specialization-map.md) | 17–19, 21–22 | Wireless, mobile, reverse engineering, human and physical assessments, and advanced tracks. |
| [Detection](tutorials/20-detection-engineering-incident-response-and-forensics.md) and [reporting](tutorials/23-reporting-remediation-and-retesting.md) | 20, 23 | Practice telemetry, incident response, forensics, remediation, and retesting throughout your study. |
| [Independent work](tutorials/24-capstones-portfolio-and-career-direction.md) | 24–27 | Capstones, portfolios, schedules, readiness checks, tools, templates, and glossary. |

Use the [complete tutorial index](tutorials/README.md#chapters) to open any chapter, or the [topic index](tutorials/TOPIC_INDEX.md) to find individual curriculum subtopics.

### Advanced tracks

The [specialization map](tutorials/22-advanced-specialization-map.md) helps you choose among AI/LLM security, IoT and hardware, industrial systems, telecom and radio, browser/kernel/virtualization research, blockchain, desktop/macOS/privacy, and adversary emulation. See the [specialist roadmap index](roadmaps/README.md#advanced-specialization-files) for prerequisites and links to all eight tracks.

## Try the local practice pack

The [portable examples](tutorials/examples/README.md) use synthetic data and Python's standard library. You need **Python 3.9 or newer**; no additional packages are required for this pack. Run these commands from the repository root:

```sh
python tutorials/examples/access_lab.py
python tutorials/examples/analyze_events.py
python tutorials/examples/parser_lab.py
```

Explore object authorization, build a synthetic incident timeline, and compare parser failure with deliberate input validation. Use `python3` if that is your interpreter's command. Other tutorial exercises may require the VMs, hardware, or platforms specified in their lessons.

To check the portable examples and tutorial collection:

```sh
python tutorials/examples/check_examples.py
python tutorials/tools/build_catalog.py --check
```

The example checks exercise the local fixtures, including a temporary loopback HTTP server. The catalog check verifies curriculum retention, manifest freshness, and local tutorial links. See [coverage and validation](tutorials/COVERAGE.md) for details.

## Run the Vue + Django browser-security lab

The [Browser Security Lab](labs/browser_security/README.md) turns the [CSP/XSS reference examples](CSP_XSS_HARMLESS_TESTS.md) into interactive localhost exercises for XSS, CSP, JSONP, stored input, and file uploads. Additional lessons compare vulnerable and fixed behavior for [path traversal](labs/browser_security/PATH_TRAVERSAL.md), [SQL injection](labs/browser_security/SQL_INJECTION.md), [access control](labs/browser_security/ACCESS_CONTROL.md), and [CSRF/CORS](labs/browser_security/CSRF_CORS.md), using disposable files and synthetic records. The lab includes a Vue interface, Django APIs, isolated experiment frames, and automated checks. Python 3.12+ and Node.js 24 LTS are required. The launcher starts the dashboard on port 8766 and a restricted companion origin on port 8767.

```powershell
python labs/browser_security/run_lab.py --setup
python labs/browser_security/run_lab.py
```

The same interface also includes [authentication/session lifecycle](labs/browser_security/AUTH_SESSIONS.md), [SSRF with local mock services](labs/browser_security/SSRF.md), and [business logic/race conditions](labs/browser_security/BUSINESS_LOGIC.md). These lessons use disposable synthetic fixtures and show vulnerable and fixed results side by side.

Continue with [template injection](labs/browser_security/TEMPLATE_INJECTION.md), [command/argument injection](labs/browser_security/COMMAND_INJECTION.md), and [XML external entities](labs/browser_security/XML_ENTITIES.md). These lessons use predefined harmless fixtures with real Django rendering, marker-producing processes, and XML parsing.

API lessons add [write authorization and mass assignment](labs/browser_security/API_WRITES.md), [JWT validation](labs/browser_security/JWT_VALIDATION.md), and [webhook replay protection](labs/browser_security/WEBHOOKS.md). Inspect stored changes, token decisions, and duplicate-event effects with fictional profiles and disposable ledgers.

Content-handling lessons add [Markdown/rich-text sanitization](labs/browser_security/SANITIZATION.md), [cross-frame postMessage security](labs/browser_security/POSTMESSAGE.md), and [ZIP extraction boundaries](labs/browser_security/ARCHIVE_EXTRACTION.md). Compare saved browser output, real sender identities, and bounded filesystem writes through the same dashboard.

Open **http://127.0.0.1:8766/**. See the lab README for sample files, policy expectations, and tests.

## Keep useful evidence

| Resource | Use it to |
| --- | --- |
| [Reusable templates](tutorials/templates/README.md) | Record scope, learning notes, tests, findings, evidence, changes, and retests. |
| [Templates and glossary](tutorials/27-reusable-templates-and-glossary.md) | Build consistent notes and look up curriculum terminology. |
| [Tutorial progress tracker](tutorials/PROGRESS.md) | Track evidence and proficiency separately from reading completion. |
| [Study schedules and readiness checks](tutorials/25-study-schedules-and-readiness-checks.md) | Plan your time and decide what needs more practice. |
| [Coverage map](tutorials/COVERAGE.md) | Trace the tutorials back to the expanded source curriculum. |

For each exercise, predict the result, observe what happens, explain the cause, make a correction, and repeat the check. Review artifacts for sensitive data before publishing them.

## Contribute

Found a broken link, unclear explanation, or reproducible error? [Open an issue](https://github.com/hareramray/Ethical-hacking/issues) with the affected file and a concrete example. Browse the [repository labels](https://github.com/hareramray/Ethical-hacking/labels) to find related work.

Pull requests for corrections, clearer lessons, and bounded practice examples are welcome. Describe the learning objective and how you checked the change; run the relevant commands above when editing the tutorials or examples.

## Support the project

[![Sponsor hareramray on GitHub](https://img.shields.io/badge/Sponsor_hareramray-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/hareramray)

Support the tutorials, practice exercises, and ongoing maintenance.

Maintainer reference: [sponsorship and label setup](.github/REPOSITORY_SETUP.md).
