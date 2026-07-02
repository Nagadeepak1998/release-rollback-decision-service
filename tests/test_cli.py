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
    assert "# Rollback Decision Review" in markdown_report.read_text(encoding="utf-8")
