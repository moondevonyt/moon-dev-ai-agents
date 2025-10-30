# Moon Dev Trading Agents - Claude Skill

**Claude skill for mastering Moon Dev's AI trading system.**

---

## What This Skill Does

Provides Claude with expert knowledge about Moon Dev's trading system:
- 48+ specialized AI agents
- Multi-exchange support (Hyperliquid, BirdEye, Extended)
- LLM provider abstraction (6 providers)
- Backtesting with RBI agent
- Trading workflows and development patterns

---

## Skill Structure

**SKILL.md** (10KB)
- Main skill file with YAML frontmatter
- Quick start commands
- Core architecture overview
- Common tasks and patterns

**AGENTS.md** (10KB)
- Complete list of all 48+ agents
- Agent descriptions by category
- When to use which agent
- Agent selection guide

**WORKFLOWS.md** (12KB)
- Practical development workflows
- Exchange configuration
- AI model switching
- Backtesting strategies
- Trading execution examples
- Debugging tips

**ARCHITECTURE.md** (15KB)
- Deep system architecture
- Component breakdown
- Data flow patterns
- Risk management layer
- Security architecture
- Scalability considerations

---

## How It Works

Uses Claude's 3-level skill loading:

**Level 1** (Always loaded): Skill name + description (~100 tokens)

**Level 2** (When triggered): SKILL.md full content (~2,000 tokens)

**Level 3** (As needed): AGENTS.md, WORKFLOWS.md, ARCHITECTURE.md

Claude automatically loads this skill when working with the trading system.

---

## Installation

This skill is already installed in this project at:
```
.claude/skills/moon-dev-trading-agents/
```

To install in your global Claude config:
```bash
cp -r .claude/skills/moon-dev-trading-agents ~/.claude/skills/
```

---

## Usage

Just start working with the repository! Claude will automatically detect when to use this skill based on the description:

- "How do I run the trading agent?"
- "What agents are available?"
- "How do I switch exchanges?"
- "How does the RBI agent work?"

Claude loads the skill and provides expert guidance.

---

## Benefits

✅ **Instant Expertise**: Any Claude instance can master this repo

✅ **Comprehensive**: Covers all 48+ agents, exchanges, workflows

✅ **Progressive Loading**: Only loads what's needed (token efficient)

✅ **Always Updated**: Skill lives in repo, stays current

✅ **Portable**: Works in Claude Code, Claude.ai, API

---

## Maintenance

Update skill files as the system evolves:
- Add new agents to AGENTS.md
- Add new workflows to WORKFLOWS.md
- Update architecture in ARCHITECTURE.md
- Keep SKILL.md in sync with major changes

---

**Built with 🌙 by Moon Dev**

*Skills enable Claude to master complex systems instantly.*
