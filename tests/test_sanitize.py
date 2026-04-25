from src.sanitize import sanitize_filename


class TestSanitizeFilename:
    def test_removes_illegal_chars(self):
        assert sanitize_filename('abc\\/:*?"<>|.mp3') == "abc.mp3"

    def test_removes_control_chars(self):
        assert sanitize_filename("ab\x00c\x1fd.mp3") == "abcd.mp3"

    def test_collapses_spaces(self):
        assert sanitize_filename("a    b   c.mp3") == "a b c.mp3"

    def test_truncates_long(self):
        name = "长" * 300 + ".mp3"
        result = sanitize_filename(name, max_len=200)
        assert len(result) <= 200
        assert result.endswith(".mp3")

    def test_keeps_chinese(self):
        assert sanitize_filename("最炫民族风 - 凤凰传奇.mp3") == "最炫民族风 - 凤凰传奇.mp3"

    def test_strips_leading_dot(self):
        assert sanitize_filename(".hidden.mp3") == "hidden.mp3"

    def test_empty_fallback(self):
        assert sanitize_filename("///\\\\:::.mp3") == "_.mp3"

    def test_no_extension(self):
        assert sanitize_filename("abc") == "abc"
