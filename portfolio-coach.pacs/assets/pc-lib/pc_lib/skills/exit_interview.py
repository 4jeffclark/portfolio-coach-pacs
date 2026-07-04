"""Exit interview skill."""

from __future__ import annotations

from pc_lib.canonical import work_dir
from pc_lib.cli import SkillArgs, SkillResult


def run(args: SkillArgs) -> SkillResult:
    out = work_dir(args.workspace, "exit-interview")
    path = out / "ExitInterview.md"

    lines = [
        "# Exit Interview",
        "",
        "## Review prompts",
        "",
        "- What was most useful in this review?",
        "- What follow-up actions will you take?",
        "- Any process or data gaps to address?",
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
                "When the user is not present (fire-and-forget run), do **not** leave prompts unanswered. "
                "Instead, record **agent preliminary observations** under this heading and mark "
                "`User responses: deferred` in the Inputs Resolved appendix.",
                "",
                "### Agent preliminary observations",
                "",
                "_Agent records datastore-specific observations from this run (coverage gaps, "
                "export cadence, data quality flags). Not a substitute for live user Q&A._",
                "",
            ]
        )
    else:
        lines.append("_Agent records verbatim Q&A here._")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return SkillResult(
        skill="exit-interview",
        status="ok",
        artifacts=[str(path)],
        messages=[
            "Prepared exit interview artifact with unattended-execution guidance; "
            "embed verbatim responses or agent observations in Report Appendix E"
        ],
    )
