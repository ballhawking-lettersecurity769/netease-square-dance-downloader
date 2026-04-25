from src.dedupe import normalize_title, Deduper


class TestNormalizeTitle:
    def test_strips_paren_dj_version(self):
        assert normalize_title("最炫民族风 (DJ版)") == normalize_title("最炫民族风")

    def test_strips_fullwidth_paren(self):
        assert normalize_title("最炫民族风（DJ版）") == normalize_title("最炫民族风")

    def test_strips_square_brackets(self):
        assert normalize_title("最炫民族风【广场舞】") == normalize_title("最炫民族风")

    def test_strips_remix_suffix(self):
        assert normalize_title("最炫民族风 Remix") == normalize_title("最炫民族风")

    def test_strips_full_version(self):
        assert normalize_title("最炫民族风 - 完整版") == normalize_title("最炫民族风")

    def test_strips_karaoke(self):
        assert normalize_title("最炫民族风（伴奏）") == normalize_title("最炫民族风")

    def test_different_songs_not_merged(self):
        assert normalize_title("红山果") != normalize_title("红山果之恋")

    def test_case_insensitive(self):
        assert normalize_title("Small Apple") == normalize_title("small apple")

    def test_empty_input(self):
        assert normalize_title("") == ""


class TestDeduper:
    def test_first_wins(self):
        d = Deduper()
        r1 = d.add({"id": 1, "name": "最炫民族风"})
        r2 = d.add({"id": 2, "name": "最炫民族风 (DJ版)"})
        assert r1 is True
        assert r2 is False
        assert len(d.items) == 1
        assert d.items[0]["id"] == 1

    def test_different_songs_both_kept(self):
        d = Deduper()
        d.add({"id": 1, "name": "红山果"})
        d.add({"id": 2, "name": "红山果之恋"})
        assert len(d.items) == 2

    def test_returns_norm_key(self):
        d = Deduper()
        d.add({"id": 1, "name": "小苹果"})
        assert d.items[0]["norm_key"] == normalize_title("小苹果")

    def test_empty_name_skipped(self):
        d = Deduper()
        assert d.add({"id": 1, "name": ""}) is False
        assert len(d.items) == 0
