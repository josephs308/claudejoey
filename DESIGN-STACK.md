# AI Design Stack

Design skills for Claude Code, installed at **project scope** — they live in this
repo, so anyone who clones it gets the same setup with no extra install steps.

## What's installed

| Piece | Where | Count |
|---|---|---|
| Emil Kowalski skills (motion, polish, UI craft) | `.claude/skills/` | 12 |
| Taste Skill (design direction, anti-generic) | `.claude/skills/` | 13 |
| Impeccable (23 commands + anti-pattern detector) | `.claude/skills/impeccable/` | 1 |
| Impeccable subagents | `.claude/agents/` | 4 |
| Impeccable detector hooks | `.claude/settings.json` | 2 |
| Playwright MCP (real browser) | `.mcp.json` | 1 |

`skills-lock.json` pins the source + content hash of every skill from the two
skill repos. Update them with `npx skills update`.

### Emil Kowalski (`emilkowalski/skill`)
`animate`, `animate-expo`, `animation-vocabulary`, `apple-design`, `ask-sonner`,
`emil-design-eng`, `find-animation-opportunities`, `improve-animations`,
`pick-ui-library`, `prototype`, `review-animations`, `write-swift`

### Taste Skill (`Leonxlnx/taste-skill`)
`brandkit`, `design-taste-frontend`, `design-taste-frontend-v1`,
`full-output-enforcement`, `gpt-taste`, `high-end-visual-design`,
`image-to-code`, `imagegen-frontend-mobile`, `imagegen-frontend-web`,
`industrial-brutalist-ui`, `minimalist-ui`, `redesign-existing-projects`,
`stitch-design-taste`

### Impeccable (23 commands)
`craft`, `init`, `document`, `extract`, `live`, `adapt`, `animate`, `audit`,
`bolder`, `clarify`, `colorize`, `critique`, `delight`, `distill`, `harden`,
`onboard`, `layout`, `optimize`, `overdrive`, `polish`, `quieter`, `shape`,
`typeset`

Run as `/impeccable <command>`, e.g. `/impeccable critique`.

The detector also runs standalone:

```
.claude/skills/impeccable/scripts/impeccable detect src/
```

It flags AI-slop tells — purple/violet gradients, overused fonts (Inter, Roboto,
Geist…), low contrast, gray-on-color — plus WCAG contrast failures. The launcher
downloads its engine binary from GitHub Releases on first run (no Node needed).

Two hooks in `.claude/settings.json` run it automatically: a fast pass after each
`Edit`/`Write`, and a full pass on `Stop`. Both are guarded with `[ ! -f … ] ||`,
so they silently no-op if the engine isn't present.

## First-run steps

1. **Install a browser for Playwright, once:**

   ```
   npx playwright install chromium
   ```

   `.mcp.json` pins `--browser chromium` rather than the default `chrome`
   channel, so Playwright uses its own isolated build instead of depending on a
   Google Chrome install. Without this step the server starts but every
   navigation fails with "Executable doesn't exist".

2. **Approve the MCP server.** Open `claude` in this repo; it will prompt to
   approve the project's Playwright server. Confirm with `/mcp`.
3. **Run `/impeccable init` once.** It interviews you about the product and
   writes `PRODUCT.md`. It needs real answers, so run it when you know what
   you're building — it does not write `DESIGN.md` (that's `/impeccable shape`).

## Figma plugin

Installed separately at **user scope** (it's tied to your account, not this repo):

```
claude plugin install figma@claude-plugins-official
```

Plugin capabilities load at startup, so a fresh session is needed after
installing. Full features need a Figma Dev or Full seat.

## The Impeccable engine binary

The markdown guidance — `SKILL.md` and 19 of the 35 reference docs — is plain
text and works with nothing installed. The other 16 docs shell out to a compiled
engine binary for `detect`, `live`, `context`, `document`, `hook`, and `ignores`.

The launcher fetches that binary from GitHub Releases on first use and verifies
it against a published SHA-256 before caching it in `~/.impeccable/bin/`. It is a
platform binary, so it can't be read the way the JS shim can — the same trust
posture as any native npm dependency (esbuild, swc, sharp).

To use the guidance without ever fetching it, delete the two `hooks` entries from
`.claude/settings.json`. Nothing else changes.

## Typical loop

1. Describe the site you want.
2. `/impeccable critique` — find what's weak.
3. `/impeccable polish` — fix the key sections.
4. Ask Claude to open the page with Playwright, screenshot it, and click through.
