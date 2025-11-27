# AI Prompt Examples from Moon Dev Trading Agents

This document catalogs the AI prompts used across various agents in the Moon Dev trading system, along with analysis of their design patterns and effectiveness.

---

## Table of Contents
1. [Trading Decision Prompt](#1-trading-decision-prompt)
2. [Strategy Idea Generator Prompt](#2-strategy-idea-generator-prompt)
3. [Video Intro Generator Prompt](#3-video-intro-generator-prompt)
4. [RBI Strategy Analyzer Prompt](#4-rbi-strategy-analyzer-prompt)
5. [Compliance Analyzer Prompt](#5-compliance-analyzer-prompt)
6. [Key Patterns Observed](#key-patterns-observed)
7. [Recommendations](#recommendations)

---

## 1. Trading Decision Prompt

**Location:** `src/agents/trading_agent.py` (lines 34-60)

**Purpose:** Analyzes market data to make buy/sell/hold trading decisions

### The Prompt

```python
TRADING_PROMPT = """
You are Moon Dev's AI Trading Assistant 🌙

Analyze the provided market data and strategy signals (if available) to make a trading decision.

Market Data Criteria:
1. Price action relative to MA20 and MA40
2. RSI levels and trend
3. Volume patterns
4. Recent price movements

{strategy_context}

Respond in this exact format:
1. First line must be one of: BUY, SELL, or NOTHING (in caps)
2. Then explain your reasoning, including:
   - Technical analysis
   - Strategy signals analysis (if available)
   - Risk factors
   - Market conditions
   - Confidence level (as a percentage, e.g. 75%)

Remember:
- Moon Dev always prioritizes risk management! 🛡️
- Never trade USDC or SOL directly
- Consider both technical and strategy signals
"""
```

### Analysis

**Strengths:**
- **Clear format specification**: The "First line must be..." instruction makes parsing trivial and reliable
- **Structured reasoning**: Breaking down the explanation into sub-bullets ensures comprehensive analysis
- **Risk-first approach**: Explicitly reminds the AI about risk management priorities
- **Domain constraints**: Hardcodes important rules like not trading USDC/SOL directly
- **Parseable action keywords**: Using caps keywords (BUY/SELL/NOTHING) makes regex extraction foolproof

**Design Pattern:** **Format-First Decision Making**
- Forces the AI to commit to a decision before explaining
- Prevents hedging or ambiguous responses
- Enables deterministic code parsing

**Potential Improvements:**
- Could add confidence thresholds (e.g., "Only BUY if confidence > 70%")
- Could specify what happens if data is missing or incomplete
- Might benefit from examples of good vs bad reasoning

**Effectiveness Rating:** 9/10
- Highly reliable for production use
- Clear separation between decision and analysis
- Easy to parse and act upon

---

## 2. Strategy Idea Generator Prompt

**Location:** `src/agents/research_agent.py` (lines 19-39)

**Purpose:** Generates unique trading strategy ideas for backtesting

### The Prompt

```python
IDEA_GENERATION_PROMPT = """
You are Moon Dev's Trading Strategy Idea Generator 🌙

Come up with ONE unique trading strategy idea that can be backtested
The idea should be innovative, specific, and concise (1-2 sentences only).

Focus on one of these areas:
- Technical indicators with unique combinations
- Volume patterns
- Volatility-based strategies
- Liquidation events
- technical indicators that can be backtested

Your response should be ONLY the strategy idea text - no explanations, no introductions,
no numbering, and no extra formatting. Just the raw idea in 1-2 sentences.

Example good responses:
"A mean-reversion strategy that enters when RSI diverges from price action while volume decreases, with exits based on ATR multiples."
"Identify market regime shifts using a combination of volatility term structure and options skew, trading only when both align."
"""
```

### Analysis

**Strengths:**
- **Few-shot learning**: Provides 2 concrete examples of desired output format
- **Constraint-driven**: "1-2 sentences only" prevents rambling
- **Negative constraints**: Explicitly states what NOT to include (no explanations, no introductions)
- **Scoped creativity**: Lists specific areas to focus on, preventing off-topic ideas
- **Raw output**: "Just the raw idea" makes it easy to feed into next stage

**Design Pattern:** **Few-Shot Constrained Generation**
- Uses examples to teach format implicitly
- Combines positive examples with negative constraints
- Balances creativity (unique ideas) with structure (1-2 sentences)

**Potential Improvements:**
- Could add a "bad example" to show what to avoid
- Might benefit from specifying technical feasibility (e.g., "must be implementable in backtesting.py")
- Could request a specific format like "If [condition], then [action]"

**Effectiveness Rating:** 8/10
- Excellent use of examples
- Good balance between creativity and structure
- Minor risk of overly complex or unbuildable ideas

---

## 3. Video Intro Generator Prompt

**Location:** `src/agents/clips_agent.py` (lines 115-132)

**Purpose:** Creates exciting video intro copy from video transcripts

### The Prompt

```python
TRANSCRIPT_PROMPT = """
{transcript}

🔥 INSTRUCTIONS START HERE 🔥
================================

YOUR ONLY JOB IS TO WRITE 2-3 EXCITING SENTENCE BASED ON THE ABOVE TRANSCRIPT INTRODUCING THE TOPIC

USE THE CONTEXT OF THE ABOVE TRANSCRIPT TO WRITE 2-3 EXCITING INTRO SENTENCES BASED ON THE TRANSRIPT

THAT'S IT. NOTHING ELSE. JUST 2-3 HYPE SENTENCES BASED ON THE TRANSCRIPT THAT INTRODUCES THE TOPIC AND GETS THEM EXCITED TO LEARN MORE AND WATCH THE FULL VIDEO

YOU ARE WRITING THE INTRO FOR A VIDEO ABOUT THE ABOVE TRANSCRIPT, 3 SENTENCES MAX. NO EMOJIS!!!!

YOU MUST USE THE TRANSCRIPT ABOVE TO WRITE THE INTRO, MAKE SURE THAT IT IS ON TOPIC

RAW TEXT ONLY. NO MARKDOWN. NO QUOTES. NO ANALYSIS. NO THINKING. JUST THE INTRO.
"""
```

### Analysis

**Strengths:**
- **CAPS for emphasis**: Uses capitalization strategically to stress critical constraints
- **Repetition technique**: States the same requirement multiple ways to ensure compliance
- **Visual separation**: The "🔥 INSTRUCTIONS START HERE 🔥" clearly delineates context from instructions
- **Explicit negatives**: "NO EMOJIS!!!!", "NO MARKDOWN", "NO QUOTES" - very clear about unwanted outputs
- **Context-first design**: Puts the transcript BEFORE the instructions so the AI reads it first

**Design Pattern:** **Aggressive Constraint Enforcement**
- Uses repetition to override AI's default behaviors (like adding markdown)
- CAPS and exclamation marks create strong "emphasis signals"
- Multiple negative constraints to prevent common LLM hallmarks

**Potential Improvements:**
- The repetition, while effective, makes the prompt verbose
- Could consolidate into a more concise instruction block
- Might benefit from a single example of desired output

**Effectiveness Rating:** 7/10
- Very effective at preventing unwanted formatting
- The aggressive style works but feels heavy-handed
- Repetition ensures compliance but reduces token efficiency

**Interesting Note:** This is a great example of "prompt engineering through frustration" - you can tell the developer iterated this after getting markdown-formatted responses repeatedly!

---

## 4. RBI Strategy Analyzer Prompt

**Location:** `src/agents/rbi_agent.py` (lines 144-182)

**Purpose:** Extracts trading strategy details from videos/PDFs and creates structured output with unique naming

### The Prompt

```python
RESEARCH_PROMPT = """
You are Moon Dev's Research AI 🌙

IMPORTANT NAMING RULES:
1. Create a UNIQUE TWO-WORD NAME for this specific strategy
2. The name must be DIFFERENT from any generic names like "TrendFollower" or "MomentumStrategy"
3. First word should describe the main approach (e.g., Adaptive, Neural, Quantum, Fractal, Dynamic)
4. Second word should describe the specific technique (e.g., Reversal, Breakout, Oscillator, Divergence)
5. Make the name SPECIFIC to this strategy's unique aspects

Examples of good names:
- "AdaptiveBreakout" for a strategy that adjusts breakout levels
- "FractalMomentum" for a strategy using fractal analysis with momentum
- "QuantumReversal" for a complex mean reversion strategy
- "NeuralDivergence" for a strategy focusing on divergence patterns

BAD names to avoid:
- "TrendFollower" (too generic)
- "SimpleMoving" (too basic)
- "PriceAction" (too vague)

Output format must start with:
STRATEGY_NAME: [Your unique two-word name]

Then analyze the trading strategy content and create detailed instructions.
Focus on:
1. Key strategy components
2. Entry/exit rules
3. Risk management
4. Required indicators

Your complete output must follow this format:
STRATEGY_NAME: [Your unique two-word name]

STRATEGY_DETAILS:
[Your detailed analysis]

Remember: The name must be UNIQUE and SPECIFIC to this strategy's approach!
"""
```

### Analysis

**Strengths:**
- **Positive and negative examples**: Shows both good and bad naming examples with explanations
- **Structured output markers**: Uses `STRATEGY_NAME:` and `STRATEGY_DETAILS:` as parseable labels
- **Numbered rules**: Makes complex requirements digestible
- **Specificity enforcement**: Explicitly prevents generic naming through examples
- **Template-like format**: The "must follow this format" section provides a clear skeleton

**Design Pattern:** **Structured Extraction with Quality Control**
- Combines creative naming with strict formatting
- Uses positive/negative examples to shape quality
- Employs parseable markers for downstream code processing
- Balances flexibility (creative naming) with structure (required fields)

**Potential Improvements:**
- Could specify what to do if the content doesn't contain enough detail
- Might benefit from a maximum length for STRATEGY_DETAILS
- Could add validation rules for the name (e.g., "no special characters")

**Effectiveness Rating:** 9/10
- Excellent balance between creativity and structure
- The positive/negative examples are highly effective
- Easy to parse in code with simple string splitting
- Prevents common pitfalls (generic naming)

**Standout Feature:** The explicit "BAD names to avoid" section is brilliant - it preemptively blocks low-quality outputs.

---

## 5. Compliance Analyzer Prompt

**Location:** `src/agents/compliance_agent.py` (lines 54-88)

**Purpose:** Analyzes ad content for Facebook advertising guidelines compliance

### The Prompt

```python
COMPLIANCE_PROMPT = """
You are Moon Dev's Compliance Agent 🌙, an expert in analyzing ads for compliance with Facebook's advertising guidelines.

Your task is to analyze the provided ad frames and transcript to determine if they comply with Facebook's advertising guidelines.

For each ad, you will:
1. Analyze each frame for visual compliance issues
2. Analyze the transcript for text/audio compliance issues
3. Check for specific violations of Facebook's guidelines
4. Provide an overall compliance rating (0-100%)
5. Identify specific issues that need to be fixed
6. Provide recommendations for improving compliance

Common compliance issues to check for:
- Personal attributes (assuming characteristics about the viewer)
- Sensational content (shocking, scary, or violent imagery)
- Adult content or nudity
- Misleading claims or false information
- Health claims without proper disclaimers
- Before/after images that imply unrealistic results
- Targeting sensitive categories (race, religion, etc.)
- Prohibited products or services
- Text-to-image ratio issues

Your analysis should be thorough but concise. Focus on actionable feedback.

Your response MUST follow this format:
{
  "compliance_status": "compliant" or "non-compliant",
  "overall_assessment": "Brief overall assessment",
  "moon_dev_message": "A fun message mentioning Moon Dev 🌙"
}

Remember to be thorough but fair in your assessment. The goal is to help improve ad compliance, not to reject ads unnecessarily.
"""
```

### Analysis

**Strengths:**
- **JSON output format**: Specifies exact structure for reliable parsing
- **Comprehensive checklist**: Lists 9 specific compliance issues to check
- **Expert positioning**: "expert in analyzing ads" sets the tone and context
- **Balanced guidance**: "thorough but fair" prevents overly strict interpretations
- **Actionable focus**: Emphasizes "actionable feedback" over abstract analysis
- **Field name specification**: Exact field names ("compliance_status", "overall_assessment") prevent variations

**Design Pattern:** **Structured Data Extraction**
- Uses JSON for machine-readable output
- Provides a domain knowledge checklist
- Balances completeness with conciseness
- Sets appropriate "tone" for decision-making (fair, not punitive)

**Potential Improvements:**
- Could provide an example JSON output
- Might specify what to do if frames/transcript are missing
- Could add a "confidence" field to the JSON output
- The format says "for each ad" but the JSON structure seems to handle only one ad

**Effectiveness Rating:** 8/10
- Clean JSON output is excellent for parsing
- Good domain-specific checklist
- Minor ambiguity about handling multiple ads
- Would benefit from example output

**Production Note:** This is a great example of using LLMs for domain-specific evaluation tasks where the rules are well-defined but require judgment.

---

## Key Patterns Observed

### 1. **Format-First Architecture**
Almost every prompt starts by defining the output format before describing the task. This is critical for production reliability.

**Example:**
```
First line must be: BUY, SELL, or NOTHING
Then explain your reasoning...
```

**Why it works:**
- LLMs are better at following format when it's stated first
- Code can parse the first line without NLP complexity
- Reduces ambiguity in AI responses

---

### 2. **Negative Constraints**
The prompts heavily use "NO X" and "NEVER Y" to override default LLM behaviors.

**Examples:**
- "NO EMOJIS!!!!"
- "NO MARKDOWN"
- "NO QUOTES"
- "Never trade USDC or SOL directly"

**Why it works:**
- LLMs have strong default behaviors (markdown formatting, helpful preambles)
- Negative constraints explicitly suppress these defaults
- Repetition and caps increase compliance

---

### 3. **Parseable Markers**
Using labels like `STRATEGY_NAME:` and `STRATEGY_DETAILS:` makes string parsing trivial.

**Pattern:**
```python
# In prompt
STRATEGY_NAME: [Your name here]
STRATEGY_DETAILS: [Your details here]

# In code
name = response.split("STRATEGY_NAME:")[1].split("\n")[0].strip()
details = response.split("STRATEGY_DETAILS:")[1].strip()
```

**Why it works:**
- Deterministic parsing without regex complexity
- Immune to minor formatting variations
- Clear structure for both AI and code

---

### 4. **Few-Shot Examples**
Several prompts provide 2-5 examples of good (and bad) outputs.

**Effectiveness:**
- More effective than lengthy explanations
- Shows rather than tells
- Especially powerful for creative tasks with constraints

**Best Practice:** Include both positive and negative examples when quality control is important.

---

### 5. **Role-Based Framing**
Every prompt starts with "You are Moon Dev's [X] Agent 🌙"

**Purpose:**
- Sets context and expertise level
- Creates consistent brand voice
- Establishes the AI's "mindset" for the task

**Subtle benefit:** This framing can improve response quality by activating relevant training data patterns.

---

### 6. **Constraint Layering**
The prompts use multiple types of constraints simultaneously:

1. **Format constraints**: "Must follow this format..."
2. **Length constraints**: "1-2 sentences only"
3. **Content constraints**: "Focus on these areas..."
4. **Quality constraints**: "Must be unique and specific"
5. **Negative constraints**: "NO markdown, NO emojis"

**Why it works:**
- Each constraint type handles a different failure mode
- Layering creates a "net" that catches most edge cases
- Defense in depth for prompt engineering

---

### 7. **JSON for Structured Data**
When the output needs to be machine-processed, JSON format is specified explicitly.

**Best Practice from compliance_agent:**
```python
Your response MUST follow this format:
{
  "compliance_status": "compliant" or "non-compliant",
  "overall_assessment": "Brief overall assessment",
  "moon_dev_message": "A fun message mentioning Moon Dev 🌙"
}
```

**Why JSON:**
- Native Python parsing with `json.loads()`
- Enforces field names and structure
- Handles complex nested data better than custom parsing

---

## Recommendations

### For Trading Agents (High Stakes)

**Best Practices:**
1. ✅ Use format-first design (decision on first line)
2. ✅ Require confidence scores/percentages
3. ✅ Add multiple negative constraints for critical rules
4. ✅ Request explicit reasoning after decision
5. ✅ Use caps keywords for actions (BUY/SELL/NOTHING)

**Example Template:**
```
You are [Agent Name]

Analyze the data and make a decision.

CRITICAL RULES:
- [Rule 1]
- [Rule 2]

Your response must follow this EXACT format:
1. First line: [ACTION] (one of: OPTION1, OPTION2, OPTION3)
2. Confidence: [0-100]%
3. Reasoning: [Your analysis]

Example good response:
OPTION1
Confidence: 75%
Reasoning: [detailed explanation]
```

---

### For Content Generation Agents

**Best Practices:**
1. ✅ Use heavy negative constraints ("NO markdown", "NO quotes")
2. ✅ Specify tone and style explicitly
3. ✅ Use CAPS and repetition for emphasis
4. ✅ Provide 2-3 example outputs
5. ✅ Put content before instructions

**Example Template:**
```
[Context/content to analyze]

🔥 INSTRUCTIONS 🔥

Write [X] about the above content.

Requirements:
- [Length constraint]
- [Style requirement]
- [Tone requirement]

DO NOT include:
- NO [unwanted element 1]
- NO [unwanted element 2]

Example good output:
"[Example 1]"
"[Example 2]"

RAW TEXT ONLY. START NOW.
```

---

### For Data Extraction Agents

**Best Practices:**
1. ✅ Use JSON format for structured output
2. ✅ Specify exact field names
3. ✅ Provide comprehensive checklists
4. ✅ Include data validation rules
5. ✅ Show example JSON output

**Example Template:**
```
You are an expert [domain] analyst.

Analyze the provided data for:
1. [Aspect 1]
2. [Aspect 2]
3. [Aspect 3]

Checklist of items to evaluate:
- [Item 1]
- [Item 2]
- [Item 3]

Your response MUST be valid JSON in this exact format:
{
  "field_name_1": "value or description",
  "field_name_2": 0-100,
  "field_name_3": ["list", "of", "items"]
}

Example output:
{
  "field_name_1": "example value",
  "field_name_2": 85,
  "field_name_3": ["item1", "item2"]
}
```

---

### For Research/Analysis Agents

**Best Practices:**
1. ✅ Use structured markers (FIELD_NAME: value)
2. ✅ Provide positive AND negative examples
3. ✅ Layer multiple quality constraints
4. ✅ Request specific, actionable outputs
5. ✅ Define clear output structure

**Example Template:**
```
You are Moon Dev's Research Agent 🌙

[Task description]

Quality Requirements:
1. [Requirement 1]
2. [Requirement 2]

Examples of GOOD outputs:
- "[Example 1]" - [why it's good]
- "[Example 2]" - [why it's good]

Examples of BAD outputs:
- "[Example 1]" - [why it's bad]
- "[Example 2]" - [why it's bad]

Output format:
SECTION_1: [content]
SECTION_2: [content]
SECTION_3: [content]

Your output must be specific and actionable.
```

---

## Lessons from Moon Dev's Prompt Engineering

### 1. **Production Reliability Requires Aggressive Constraints**
These prompts don't trust the AI to "be helpful." They enforce exact formats through repetition, examples, and negative constraints. This is the right approach for automated systems.

### 2. **Few-Shot > Long Explanations**
Notice how the prompts use 2-3 examples rather than paragraphs of explanation. Examples are more effective for teaching format and quality.

### 3. **Parsing Strategy Drives Prompt Design**
Every prompt is clearly designed with downstream parsing in mind:
- First line = action keyword → `response.split('\n')[0]`
- JSON format → `json.loads(response)`
- Labeled sections → `response.split('LABEL:')[1]`

### 4. **Negative Constraints Fight Default LLM Behaviors**
LLMs are trained to be helpful, which means:
- They add markdown formatting
- They include preambles ("Certainly! Here's...")
- They add explanations when not asked
- They use emojis for friendliness

These prompts aggressively suppress these defaults because they break parsing.

### 5. **Context-First, Instructions-Second**
Notice the clips_agent puts the transcript BEFORE the instructions. This ensures the AI reads and processes the content before seeing what to do with it.

### 6. **Brand Voice is Consistent**
"You are Moon Dev's X Agent 🌙" appears in every prompt. This creates:
- Consistent personality across agents
- Clear role definition
- Implicit expertise framing

### 7. **Confidence Scores are Underutilized**
Only the trading_agent explicitly requests a confidence percentage. This would be valuable for:
- Risk management (don't act on low-confidence signals)
- Quality filtering (reject low-confidence research)
- Ensemble voting (weight by confidence)

**Recommendation:** Add confidence scores to more prompts.

---

## Common Anti-Patterns to Avoid

### ❌ Vague Output Requirements
**Bad:** "Analyze this data and provide insights"
**Good:** "First line: BUY/SELL/NOTHING. Then explain in 3 bullet points."

### ❌ Trusting Default Formatting
**Bad:** Assuming the AI won't use markdown
**Good:** "RAW TEXT ONLY. NO MARKDOWN."

### ❌ Missing Examples
**Bad:** "Be creative but specific"
**Good:** "Examples of good ideas: [example 1], [example 2]"

### ❌ Unclear Parsing Strategy
**Bad:** Free-form text that requires NLP to parse
**Good:** JSON or labeled sections (FIELD_NAME: value)

### ❌ Single Constraint Type
**Bad:** Only format constraints
**Good:** Layer format + length + content + quality constraints

---

## Conclusion

The Moon Dev AI prompts demonstrate **production-grade prompt engineering** for automated trading systems. Key takeaways:

1. **Reliability over elegance**: Aggressive constraints and repetition ensure consistent outputs
2. **Parse-first design**: Every prompt is designed for downstream code parsing
3. **Defense in depth**: Multiple constraint layers catch different failure modes
4. **Examples > explanations**: Few-shot learning is more effective than lengthy instructions
5. **Format-first architecture**: Decision/action comes first, reasoning comes second

These patterns are directly applicable to any production AI system where reliability and parseability are critical.

**Overall System Rating: 8.5/10**
- Excellent production practices
- Clear parsing strategies
- Consistent design patterns
- Could benefit from more confidence scores and example outputs
- Some prompts could be more token-efficient

The aggressive constraint style might feel heavy-handed in isolation, but it's exactly right for production systems that need to run autonomously 24/7 without human review.
