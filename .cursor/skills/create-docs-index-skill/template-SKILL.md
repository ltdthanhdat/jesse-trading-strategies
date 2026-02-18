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
| Docker setup | https://docs.xxx.com/docker |

### API / Reference
| Topic | Link |
|-------|------|
| API Reference | https://docs.xxx.com/api |
| Methods and properties | https://docs.xxx.com/api/methods |
| Examples | https://docs.xxx.com/api/examples |

### Configuration & advanced
| Topic | Link |
|-------|------|
| Configuration | https://docs.xxx.com/config |
| Advanced topics | https://docs.xxx.com/advanced |
| Best practices | https://docs.xxx.com/best-practices |

### Debugging & troubleshooting
| Topic | Link |
|-------|------|
| Debugging guide | https://docs.xxx.com/debugging |
| Common issues | https://docs.xxx.com/troubleshooting |

---

## Quick reference (optional)
- **Key command**: `[command]`
- **Requirements**: [requirements]
- **Home**: https://docs.xxx.com
