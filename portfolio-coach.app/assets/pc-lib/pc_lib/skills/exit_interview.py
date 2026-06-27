"""Exit interview skill."""

from __future__ import annotations

from pc_lib.canonical import work_dir
from pc_lib.cli import SkillArgs, SkillResult
from pc_lib.skills._confirm import write_review_template


def run(args: SkillArgs) -> SkillResult:
    out = work_dir(args.workspace, "exit-interview")
    path = write_review_template(
        out / "ExitInterview.md",
        "Exit Interview",
        [
            "What was most useful in this review?",
            "What follow-up actions will you take?",
            "Any process or data gaps to address?",
        ],
    )
    return SkillResult(
        skill="exit-interview",
        status="ok",
        artifacts=[str(path)],
        messages=["Prepared exit interview template; embed verbatim responses in Report Appendix E"],
    )
