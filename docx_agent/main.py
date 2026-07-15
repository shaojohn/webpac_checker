"""Main entry point for the DOCX proofreading agent.

Usage
-----
Run with a specific file::

    python -m docx_agent.main path/to/document.docx

Run with the built-in sample document::

    python -m docx_agent.main

Use the LLM-driven mode (requires OPENAI_API_KEY in environment)::

    OPENAI_API_KEY=sk-... python -m docx_agent.main path/to/document.docx --llm
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docx_agent.agent.proofreading_agent import ProofreadingAgent
from docx_agent.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from docx_agent.report.html_reporter import HtmlReporter
from docx_agent.utils.logger import get_logger

_logger = get_logger("docx_agent.main")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="docx_agent",
        description="Proofread a DOCX file and generate an HTML report.",
    )
    parser.add_argument(
        "docx_path",
        nargs="?",
        default=str(Path(__file__).parent / "sample_docx" / "sample.docx"),
        help="Path to the .docx file to proofread (default: sample.docx).",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use the LLM-driven mode (requires OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory where the HTML report will be saved.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose LangChain output (only with --llm).",
    )

    args = parser.parse_args(argv)

    docx_path = Path(args.docx_path)
    if not docx_path.exists():
        _logger.error("File not found: %s", docx_path)
        print(f"Error: File not found: {docx_path}", file=sys.stderr)
        return 1

    _logger.info("=== DOCX Proofreading Agent ===")
    _logger.info("Target file : %s", docx_path)
    _logger.info("Mode        : %s", "LLM" if args.llm else "deterministic")

    # Create agent
    agent = ProofreadingAgent(
        openai_api_key=OPENAI_API_KEY,
        model_name=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
    )

    # Run proofreading
    if args.llm:
        result = agent.run_with_llm(docx_path, verbose=args.verbose)
    else:
        result = agent.run(docx_path)

    # Print summary to console
    print("\n" + "=" * 60)
    print(f"  DOCX Proofreading Complete: {docx_path.name}")
    print("=" * 60)
    print(f"  Total issues : {result.total_issues}")
    print(f"    Errors     : {result.error_count}")
    print(f"    Warnings   : {result.warning_count}")
    print(f"    Info       : {result.info_count}")
    print("=" * 60)

    if result.llm_summary:
        print("\nAI Summary:")
        print(result.llm_summary)

    # Generate HTML report
    reporter = HtmlReporter(output_dir=args.output_dir)
    report_path = reporter.generate(result)
    print(f"\nHTML report saved to: {report_path}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
