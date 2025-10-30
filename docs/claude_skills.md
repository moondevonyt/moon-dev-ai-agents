# Claude Skills

Modular capabilities that extend Claude's functionality through instructions, scripts, and resources loaded automatically when needed.

---

## What Are Skills?

Skills are folders containing a `SKILL.md` file with instructions and optional resources. Claude automatically detects when to use them—no manual invocation needed.

**Key Benefits:**
- **Composable**: Stack multiple skills together
- **Portable**: Work across Claude.ai, Claude Code, and API
- **Efficient**: Only load content when needed
- **Powerful**: Include executable scripts for reliable operations

---

## Skill Structure

```
skill-name/
├── SKILL.md           # Required: Main instructions
├── REFERENCE.md       # Optional: Additional docs
├── EXAMPLES.md        # Optional: Usage examples
└── scripts/           # Optional: Executable code
    └── helper.py
```

### SKILL.md Format

Every skill requires YAML frontmatter:

```yaml
---
name: skill-name
description: Brief description of what this skill does and when to use it
---

# Skill Name

## Instructions
Step-by-step guidance for Claude on how to use this skill.

## Examples
Concrete usage examples.
```

**Field Requirements:**
- `name`: Max 64 chars, lowercase, hyphens only, no "anthropic" or "claude"
- `description`: Max 1024 chars, explain what it does and when to use it

---

## Three-Level Loading

Skills use progressive disclosure to avoid token bloat:

| Level | When Loaded | Content |
|-------|-------------|---------|
| **1: Metadata** | Always (startup) | name + description (~100 tokens) |
| **2: Instructions** | When triggered | Full SKILL.md body |
| **3: Resources** | As needed | Referenced files, scripts, templates |

**Level 1**: Claude loads all skill names/descriptions at startup to decide when to use them.

**Level 2**: When triggered, Claude reads SKILL.md from filesystem into context.

**Level 3**: Claude reads additional files or runs scripts only when needed.

This allows unlimited bundled content without hitting token limits.

---

## How Claude Uses Skills

1. **Discovery**: Claude scans installed skills at startup (Level 1 metadata)
2. **Activation**: When task matches a skill's description, Claude loads SKILL.md (Level 2)
3. **Execution**: Claude follows instructions, reads additional files as needed (Level 3)
4. **Scripts**: Claude runs bundled scripts via bash—only output enters context, not code

Skills activate automatically based on task relevance. You'll see skill activation in Claude's reasoning chain.

---

## Creating Skills

### Method 1: Use skill-creator Skill

Claude has a built-in skill that helps create new skills interactively:
1. Ask Claude to create a skill
2. skill-creator guides you through the process
3. Claude generates SKILL.md, folder structure, and bundles resources

### Method 2: Manual Creation

1. Create folder: `~/.claude/skills/your-skill-name/`
2. Create `SKILL.md` with YAML frontmatter
3. Add instructions, examples, and optional resources
4. Restart Claude or reload skills

---

## Installation

### Claude Code

**From Marketplace:**
```bash
# Install from anthropics/skills
# Search for skills in Claude Code marketplace
```

**Manual Installation:**
```bash
# Create in ~/.claude/skills/
mkdir -p ~/.claude/skills/my-skill
cd ~/.claude/skills/my-skill
# Create SKILL.md file
```

**Project-Specific:**
```bash
# Install in project: .claude/skills/
mkdir -p .claude/skills/my-skill
cd .claude/skills/my-skill
# Create SKILL.md file
```

### Claude.ai

1. Go to Settings > Features
2. Upload custom skill as .zip file
3. Skill activates automatically

### API

Requires beta headers:
- `code-execution-2025-08-25`
- `skills-2025-10-02`
- `files-api-2025-04-14`

Upload via `/v1/skills` endpoint or reference pre-built skills by ID.

---

## Best Practices

**Start Simple**: Begin with clear instructions, add complexity as needed.

**Split Large Content**: Break unwieldy SKILL.md into referenced files (REFERENCE.md, FORMS.md).

**Use Scripts**: For deterministic operations (sorting, parsing), use Python/Bash scripts instead of token generation.

**Test Iteratively**: Observe how Claude uses the skill and refine based on real usage.

**Clear Description**: Write precise descriptions so Claude knows when to activate the skill.

---

## Pre-built Skills

Anthropic provides four ready-to-use skills:
- **pptx**: PowerPoint creation and editing
- **xlsx**: Excel spreadsheets and analysis
- **docx**: Word document creation
- **pdf**: PDF generation and formatting

---

## Security

⚠️ **Only install skills from trusted sources**

Skills can:
- Execute bash commands
- Read/write files
- Run Python scripts

**Before installing:**
- Audit all bundled files
- Review script code
- Verify no malicious operations
- Check for data exfiltration risks

---

## Limitations

- **No network access**: Skills cannot make API calls
- **No runtime installs**: Cannot install packages at runtime
- **No cross-platform sync**: Upload separately for each platform
- **Scoped to user/workspace**: Cannot share publicly

---

## Example: Simple Skill

```yaml
---
name: markdown-formatter
description: Format and structure markdown documents with consistent styling
---

# Markdown Formatter

## Instructions

When asked to format markdown:

1. Check for proper heading hierarchy (H1 → H2 → H3)
2. Add blank lines between sections
3. Format code blocks with language identifiers
4. Use consistent list formatting
5. Add horizontal rules between major sections

## Examples

**Input**: "Format this markdown file"
**Action**: Read file, apply formatting rules, write formatted version

## Reference Files

See FORMATTING_RULES.md for complete style guide.
```

---

## Resources

- **Skills Cookbook**: https://github.com/anthropics/claude-cookbooks/tree/main/skills
- **API Docs**: https://docs.claude.com/en/docs/agents-and-tools/agent-skills
- **Anthropic Blog**: https://www.anthropic.com/news/skills

---

**Built by Moon Dev 🌙**

*Skills enable Claude to master specialized tasks across all surfaces.*
