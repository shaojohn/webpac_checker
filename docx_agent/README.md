# DOCX Proofreading Agent

A production-ready DOCX proofreading system built with **LangChain** and the **external skill pattern**.  
Skills are independent, reusable modules; an orchestrating agent decides how to combine them.

---

## Project Structure

```
docx_agent/
├── requirements.txt          # Python dependencies
├── config.py                 # All tuneable settings
├── main.py                   # CLI entry point
├── README.md                 # This file
│
├── skills/                   # Individual proofreading capabilities
│   ├── __init__.py
│   ├── base_skill.py         # Abstract base + SkillResult/Issue dataclasses
│   ├── docx_reader_skill.py  # Extract text, fonts, and formatting
│   ├── content_checker_skill.py  # Spell & grammar checking
│   ├── font_checker_skill.py     # Font family/size validation
│   └── format_checker_skill.py  # Paragraph, heading & table formatting
│
├── agent/                    # LangChain orchestration layer
│   ├── __init__.py
│   ├── tools.py              # StructuredTool wrappers for each skill
│   └── proofreading_agent.py # Deterministic + LLM-driven agent
│
├── report/                   # Output generation
│   ├── __init__.py
│   └── html_reporter.py      # Self-contained HTML report generator
│
├── utils/                    # Shared utilities
│   ├── __init__.py
│   ├── logger.py             # Rotating-file + console logger
│   └── validators.py         # Input validation helpers
│
└── sample_docx/
    └── sample.docx           # Test document with deliberate issues
```

---

## Requirements

- Python 3.9+
- Java 8+ (optional – only needed for grammar checking via `language-tool-python`)

### Install dependencies

```bash
cd docx_agent
pip install -r requirements.txt
```

### Optional: grammar checking

Grammar checking uses [language-tool-python](https://pypi.org/project/language-tool-python/),
which requires a local Java runtime.  Install Java and then `language-tool-python` will
automatically download the LanguageTool server on first use.

---

## Configuration

Copy `.env.example` to `.env` and set your values:

```bash
# OpenAI (only required for --llm mode)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0

# Logging
LOG_LEVEL=INFO
```

All other settings (allowed font families, size limits, heading sizes, etc.) are
in `config.py`.

---

## Usage

### CLI

```bash
# Proofread the built-in sample document
python -m docx_agent.main

# Proofread a specific file
python -m docx_agent.main path/to/my_document.docx

# Use the LLM-driven mode (requires OPENAI_API_KEY)
python -m docx_agent.main path/to/my_document.docx --llm --verbose

# Specify output directory for the HTML report
python -m docx_agent.main path/to/my_document.docx --output-dir /tmp/reports
```

### Python API

```python
from docx_agent.agent import ProofreadingAgent
from docx_agent.report import HtmlReporter

# Deterministic mode (no API key required)
agent = ProofreadingAgent()
result = agent.run("path/to/document.docx")

print(f"Found {result.total_issues} issues "
      f"({result.error_count} errors, {result.warning_count} warnings)")

# Generate HTML report
reporter = HtmlReporter(output_dir="/tmp/reports")
report_path = reporter.generate(result)
print(f"Report saved to: {report_path}")
```

```python
# LLM-driven mode
agent = ProofreadingAgent(openai_api_key="sk-...", model_name="gpt-4o")
result = agent.run_with_llm("path/to/document.docx", verbose=True)
```

---

## Architecture

### External Skill Pattern

Each skill:
1. Inherits from `BaseSkill` and implements `execute()`.
2. Accepts well-defined inputs (parsed document data or a file path).
3. Returns a `SkillResult` containing a list of `Issue` objects.

The agent orchestrates skills without knowing their implementation details —
it just calls `skill.run(...)` and collects `SkillResult` objects.

### LangChain Integration

`agent/tools.py` wraps each skill as a `StructuredTool`.  The `ProofreadingAgent`
can run in two modes:

| Mode | Description |
|------|-------------|
| **Deterministic** (`run`) | Calls every skill in a fixed order. No LLM or API key required. |
| **LLM-driven** (`run_with_llm`) | Uses a ReAct agent backed by OpenAI to decide tool order and produce an AI summary. |

### Skills

| Skill | What it checks |
|-------|---------------|
| `DocxReaderSkill` | Extracts all text, runs, tables, sections, and formatting metadata |
| `ContentCheckerSkill` | Spell checking (pyspellchecker) + grammar (LanguageTool) + heuristics |
| `FontCheckerSkill` | Font family allow-list, size range, font count diversity |
| `FormatCheckerSkill` | Heading hierarchy, alignment consistency, spacing, indentation, table structure |

---

## Output

The HTML report includes:

- **Executive summary** cards (errors / warnings / info / paragraphs / words)
- **AI summary** (when `--llm` is used)
- **Issue tables** grouped by category with colour-coded severity badges
- **Recommendations** derived from the findings

Reports are saved to `docx_agent/reports/` by default.

---

## Extending

Add a new skill in three steps:

1. Create `skills/my_new_skill.py` inheriting from `BaseSkill`.
2. Add a `StructuredTool` wrapper in `agent/tools.py`.
3. Call it in `ProofreadingAgent.run()` and `ProofreadingAgent.run_with_llm()`.

---

## License

MIT
