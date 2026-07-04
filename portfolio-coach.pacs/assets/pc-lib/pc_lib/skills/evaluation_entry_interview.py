"""Evaluation entry interview skill."""

from __future__ import annotations

from pc_lib.canonical import work_dir
from pc_lib.cli import SkillArgs, SkillResult


def run(args: SkillArgs) -> SkillResult:
    out = work_dir(args.workspace, "evaluation-entry-interview")
    path = out / "Interview.md"

    lines = [
        "# Evaluation Entry Interview",
        "",
        "## Purpose",
        "",
        "Pre-report evaluation interview after core quantification context is available. "
        "Distinct from holdings/theme/thesis map confirmation.",
        "",
        "## Review prompts",
        "",
        "- What outcome matters most from this review?",
        "- What concerns or hypotheses should the evaluation prioritize?",
        "- Any constraints on recommendations (tax, liquidity, mandate)?",
        "- What would make this review a success for you?",
        "",
        "## User responses",
        "",
    ]

    if args.evaluation:
        lines.extend(
            [
                "_When the user is present: record verbatim Q&A below._",
                "",
                "## Unattended execution",
                "",
                "When the user is not present (fire-and-forget run), record **agent preliminary "
                "observations** under this heading and mark `User responses: deferred` in the "
                "Inputs Resolved appendix. Tailor observations to the active playbook and overlay.",
                "",
                "### Agent preliminary observations",
                "",
                "_Agent records playbook-specific observations from quantification context. "
                "Not a substitute for live user Q&A._",
                "",
            ]
        )
    else:
        lines.append("_Evaluation overlay inactive — interview not required._")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return SkillResult(
        skill="evaluation-entry-interview",
        status="ok",
        artifacts=[str(path)],
        messages=[
            "Prepared evaluation entry interview template; embed in delivered report Appendix "
            "before report generation when evaluation overlay is active"
        ],
    )
