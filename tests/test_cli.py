from yt_summarizer.cli.app import parse_args


def test_parse_args_playlist():
    args = parse_args(["--playlist", "https://youtube.com/playlist?list=PL1", "--intent", "DSA"])
    assert args.playlist == "https://youtube.com/playlist?list=PL1"
    assert args.intent == "DSA"
    assert args.detail == "detailed"
    assert args.force is False
    assert args.video is None


def test_parse_args_video():
    args = parse_args(["--video", "https://youtube.com/watch?v=abc", "--intent", "DSA"])
    assert args.video == "https://youtube.com/watch?v=abc"
    assert args.intent == "DSA"


def test_parse_args_detail_brief():
    args = parse_args(["--video", "URL", "--intent", "DSA", "--detail", "brief"])
    assert args.detail == "brief"


def test_parse_args_force():
    args = parse_args(["--video", "URL", "--intent", "DSA", "--force"])
    assert args.force is True


def test_parse_args_output():
    args = parse_args(["--video", "URL", "--intent", "DSA", "--output", "./my-notes"])
    assert args.output == "./my-notes"


def test_parse_args_no_args_returns_none():
    args = parse_args([])
    assert args.playlist is None
    assert args.video is None
    assert args.intent is None
