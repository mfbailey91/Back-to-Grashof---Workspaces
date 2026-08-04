from grashof_workspace.cli import main


def test_cli_rejects_nonpositive_link_lengths(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["grashof-workspace", "--l1", "0", "--l2", "1", "--l3", "1"],
    )
    try:
        main()
    except SystemExit as exc:
        assert exc.code not in (0, None)
        return
    raise AssertionError("expected SystemExit for invalid lengths")
