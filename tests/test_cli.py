from release_rollback.cli import main


def test_review_command_writes_json_and_markdown(tmp_path) -> None:
    json_report = tmp_path / "review.json"
    markdown_report = tmp_path / "review.md"

    exit_code = main(
        [
            "review",
            "samples/post_deploy_review.json",
            "--output",
            str(json_report),
            "--markdown",
            str(markdown_report),
            "--fail-on-rollback",
        ]
    )

    assert exit_code == 2
    assert '"decision": "rollback"' in json_report.read_text(encoding="utf-8")
    assert '"execution_status": "ready"' in json_report.read_text(encoding="utf-8")
    assert "# Rollback Decision Review" in markdown_report.read_text(encoding="utf-8")


def test_audit_command_writes_ready_release_record(tmp_path) -> None:
    json_report = tmp_path / "audit.json"
    markdown_report = tmp_path / "audit.md"

    exit_code = main(
        [
            "audit",
            "samples/approval_audit.json",
            "--output",
            str(json_report),
            "--markdown",
            str(markdown_report),
            "--fail-on-block",
        ]
    )

    assert exit_code == 0
    assert '"status": "ready"' in json_report.read_text(encoding="utf-8")
    assert "# Release Approval Audit" in markdown_report.read_text(encoding="utf-8")
