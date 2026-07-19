# Static Site Visual Redesign

- Status: Draft
- Date: 2026-07-18
- Target version: Unreleased
- Prerequisite specs: none (independent of [source-tiering-and-evidence-gate](../2026-07-18-source-tiering-and-evidence-gate/README.md); only shares `build_site.py` as the output layer)

`build_site.py` currently generates `index.html` and
`history/<ts>/<Category>.html` from inline Python f-string HTML/CSS. The
result looks plain: dark mode is hardcoded off (the
`prefers-color-scheme` block is an empty no-op), the sidebar is a long
unsearchable list with no way to tell which section you're reading, and on
mobile the whole table of contents gets pushed above the content. The user
asked whether to adopt `vercel/ai` to make the GitHub Pages site prettier;
`vercel/ai` is a React/Next.js SDK for streaming chat UIs and doesn't fit a
framework-free, build-step-free Python static-HTML pipeline — adopting it
would mean bolting on a whole Node/React toolchain just for styling. This
spec keeps the site 100% static (plain HTML/CSS/vanilla JS, still generated
by `build_site.py`, no new dependencies) while redesigning the information
architecture and visuals to be genuinely readable and usable.

## Documents

- [PRD](PRD.md): problem, goals, non-goals, acceptance criteria
- [SYSTEM](SYSTEM.md): design system, template structure, boundary with the
  existing pipeline
- [TEST](TEST.md): how to verify
- [TASKS](TASKS.md): implementation and acceptance checklist

## Core Principle

```text
Still pure static output: no frontend framework, no build step, no changes
to fetch.py/summarizer.py's data formats.
Only build_site.py changes — how summary.md/history/*.md get turned into
usable HTML.
```

Category colors, dark mode, sidebar search, and scroll-highlighting all
exist to make a dense, multi-category long-form page easier to scan and
navigate — they are not decoration.
