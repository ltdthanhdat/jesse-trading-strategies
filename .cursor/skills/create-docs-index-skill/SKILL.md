---
name: create-docs-index-skill
description: Creates documentation-index skills that map topics to official doc URLs. Use when user wants to create a docs skill for a library, framework, or documentation site, or asks to "create skill docs for X", "skill link to docs of Y".
---

# Create Documentation Index Skill

This skill guides creating **docs-index skills** — skills that map topics to official documentation URLs without duplicating content. The agent uses these skills to suggest the right doc link or fetch content when needed.

## When to use this skill

- User says: "tạo skill docs cho thư viện X", "create docs skill for Y", "skill link tới docs của Z".
- User provides a docs URL and wants a skill that points to each section.
- User wants to standardize how docs-index skills are created.

---

## Core principles

1. **No duplication**: Skill only maps topic → URL, does not paste long content.
2. **One skill = one docs set**: One library/docs site = one skill (clear name like `jesse-trade`, `react-docs`).
3. **Concise**: SKILL.md stays short; details live on docs, agent fetches when needed.
4. **Description has trigger terms**: So agent knows when to apply (library name, docs name, use cases).

---

## Required inputs

Gather from user:

| Input | Description | Example |
|-------|-------------|---------|
| **Docs base URL** | Root URL of documentation | `https://docs.jesse.trade` |
| **Library/product name** | Name for skill name & description | Jesse Trade, React, FastAPI |
| **Target audience** | Who uses it | Developers writing strategies |
| **Trigger scenarios** | What user asks/does to trigger skill | "Jesse", "backtest", "routes" |

Optional:
- Sitemap/menu structure (to understand sections).
- Key URLs (Getting started, API reference, config) — can discover more.

---

## 6-step workflow

### Step 1: Discover docs structure

**Actions:**
- Open **docs base URL** (and index/overview page if available).
- Collect **main sections**: Getting started, Installation, API Reference, Configuration, Guides, etc.
- For each section, record **exact URL** (verify it opens).
- Methods:
  - Read menu/sidebar on docs site.
  - Use `site:docs.xxx.com` web search.
  - Fetch homepage/sitemap (if available) and parse links.
  - Use `mcp_web_fetch` to explore docs pages.

**Output**: List of (Topic, URL) pairs — group by category if logical.

**Example:**
```
Getting started: https://docs.jesse.trade/docs/getting-started/
Docker setup: https://docs.jesse.trade/docs/getting-started/docker
Routes: https://docs.jesse.trade/docs/routes
Strategies API: https://docs.jesse.trade/docs/strategies/api.html
```

### Step 2: Name skill and write description

**Skill name:**
- lowercase, hyphens, recognizable (e.g., `jesse-trade`, `react-docs`, `fastapi-docs`).
- Max 64 characters.

**Description** (third person, < 1024 chars):
- **WHAT**: Skill points to official docs of X, maps topic → link.
- **WHEN**: Trigger terms (library name, docs name, use cases: setup, API, config, etc.).

**Example:**
```yaml
name: jesse-trade
description: Points to official Jesse Trade documentation sections. Use when working with Jesse, algo-trading strategies, backtesting, routes, indicators, config, or when the user mentions Jesse, jesse.trade, or docs.jesse.trade.
```

### Step 3: Group topics and links into tables

**Actions:**
- Group (Topic, URL) pairs into **logical groups** (Getting started, API, Config, Debug, etc.).
- Each group = one markdown table:

```markdown
### [Group Name]

| Topic | Link |
|-------|------|
| Brief description of topic | https://... |
```

**Guidelines:**
- **Topic**: One line, enough for agent/user to know when to use that link.
- **Link**: Full URL, verified to open.

**Example grouping:**
- Getting started & setup
- Project structure & config
- API / Reference
- Debugging & research

### Step 4: Write SKILL.md

**Structure:**

```markdown
---
name: <skill-name>
description: <WHAT + WHEN description>
---

# [Library/Docs Name] — Documentation index

[One paragraph: what it is, official docs URL. This skill maps topics to doc sections; it does not duplicate content.]

## When to use this skill

- User asks about [X], [Y], [Z].
- User works with [relevant files/context].
- User mentions [docs URL] or "check the docs".

## Agent behavior

- For each topic below, suggest the doc link or use mcp_web_fetch with that URL to summarize.
- Prefer pointing to the official doc over pasting long excerpts.

---

## Documentation index

### Getting started & setup
| Topic | Link |
|-------|------|
| ... | https://... |

### API / Reference
| Topic | Link |
|-------|------|
| ... | https://... |

### Configuration & advanced
| Topic | Link |
|-------|------|
| ... | https://... |

---

## Quick reference (optional)
- [Key command or requirement]
- [Home link]
```

**Keep SKILL.md < 500 lines** (prioritize brevity; tables are the core).

### Step 5: Create docs-links.md (optional)

**Purpose:** List all URLs (one per line), no content. For quick copy-paste or script/agent use.

**Example:**
```markdown
# [Name] — Doc URLs
Base: https://docs.xxx.com
- https://docs.xxx.com/getting-started
- https://docs.xxx.com/api
- ...
```

### Step 6: Verify

**Checklist:**
- [ ] Description has trigger terms, written in third person.
- [ ] All links in index open correctly.
- [ ] Topics in tables are clear enough to choose the right link.
- [ ] SKILL.md < 500 lines.
- [ ] Agent behavior is clear: suggest link or fetch.

---

## Directory structure

```
<cursor-skills-dir>/<skill-name>/
├── SKILL.md          # Required: frontmatter + index
└── docs-links.md     # Optional: URL list
```

**Storage:**
- **Project**: `.cursor/skills/<skill-name>/` (shared with repo).
- **Global**: `~/.cursor/skills/<skill-name>/` (available across projects).
- **Never** create in `~/.cursor/skills-cursor/` (reserved).

---

## Template SKILL.md

Copy and customize:

```markdown
---
name: <skill-name>
description: Points to official [LIBRARY/DOCS] documentation. Use when [trigger scenarios and keywords].
---

# [LIBRARY/DOCS] — Documentation index

[One paragraph: what it is, official docs URL. This skill maps topics to doc sections; it does not duplicate content.]

## When to use this skill

- User asks about [X], [Y], [Z].
- User works with [relevant files/context].
- User mentions [docs URL] or "check the docs".

## Agent behavior

- For each topic below, suggest the doc link or use mcp_web_fetch with that URL to summarize.
- Prefer pointing to the official doc over pasting long excerpts.

---

## Documentation index

### Getting started & setup
| Topic | Link |
|-------|------|
| Getting started (overview, requirements) | https://docs.xxx.com/getting-started |
| Installation | https://docs.xxx.com/installation |

### API / Reference
| Topic | Link |
|-------|------|
| API Reference | https://docs.xxx.com/api |
| Methods and properties | https://docs.xxx.com/api/methods |

### Configuration & advanced
| Topic | Link |
|-------|------|
| Configuration | https://docs.xxx.com/config |
| Advanced topics | https://docs.xxx.com/advanced |

---

## Quick reference (optional)
- [Key command or requirement]
- [Home link: https://docs.xxx.com]
```

---

## Example: Jesse Trade skill

Reference: `.cursor/skills/jesse-trade/SKILL.md`

**Key points:**
- Name: `jesse-trade`
- Description includes: "Jesse", "algo-trading", "backtesting", "routes", "indicators", "config".
- Groups: Getting started & setup, Project structure & config, Strategies & API, Debugging & research.
- Each table maps clear topics to verified URLs.

---

## Variations

- **Multiple base URLs**: One skill can map main docs + blog/announcements (add separate section or table).
- **Languages**: Can have parallel skills `xxx-docs-en`, `xxx-docs-vi` if docs have multiple languages and you want clear triggers.
- **Versions**: If docs have versions (v1, v2), note in Topic (e.g., "API Reference (v2)") or split skills by version if they differ significantly.

---

## Execution checklist

When creating a docs-index skill:

1. ✅ Gather: base URL + library/docs name + trigger scenarios.
2. ✅ Discover docs structure → list (Topic, URL), group by category.
3. ✅ Set name + description (with trigger terms).
4. ✅ Write SKILL.md: overview, when to use, agent behavior, Documentation index tables.
5. ✅ (Optional) Create docs-links.md.
6. ✅ Verify: links open, description has triggers, SKILL.md < 500 lines.

---

## Tips

- Start with homepage and main navigation to understand structure.
- Use `mcp_web_fetch` to explore docs pages and extract links.
- Group logically — too many small groups is confusing; too few large groups is hard to navigate.
- Test all URLs before finalizing.
- Keep topic descriptions concise but specific enough for context matching.
