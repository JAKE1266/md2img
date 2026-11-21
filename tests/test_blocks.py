import unittest

from md2img.blocks import Block, parse_inline, parse_markdown, strip_inline


class TestInline(unittest.TestCase):
    def test_bold_and_code(self):
        runs = parse_inline("普通 **加粗** 与 `代码` 混排")
        self.assertEqual([r.style for r in runs], ["text", "bold", "text", "code", "text"])
        self.assertEqual(runs[1].text, "加粗")
        self.assertEqual(runs[3].text, "代码")

    def test_plain_text(self):
        self.assertEqual([r.text for r in parse_inline("没有标记")], ["没有标记"])

    def test_strip_inline(self):
        self.assertEqual(strip_inline("**a** `b` c"), "a b c")

    def test_unclosed_markers_are_literal(self):
        runs = parse_inline("这里有 ** 未闭合")
        self.assertTrue(all(r.style == "text" for r in runs))


class TestBlocks(unittest.TestCase):
    def test_headings(self):
        blocks = parse_markdown("# 一\n\n## 二\n\n### 三")
        self.assertEqual([b.kind for b in blocks], ["heading"] * 3)
        self.assertEqual([b.level for b in blocks], [1, 2, 3])
        self.assertEqual(blocks[0].text, "一")

    def test_lists(self):
        blocks = parse_markdown("- 甲\n- 乙\n\n1. 一\n2、二")
        kinds = [(b.kind, b.marker) for b in blocks]
        self.assertEqual(kinds, [("bullet", ""), ("bullet", ""), ("olist", "1"), ("olist", "2")])

    def test_quote_and_hr(self):
        blocks = parse_markdown("> 引用一句\n\n---")
        self.assertEqual([b.kind for b in blocks], ["quote", "hr"])
        self.assertEqual(blocks[0].text, "引用一句")

    def test_code_block(self):
        md = "```python\nprint(1)\nprint(2)\n```"
        blocks = parse_markdown(md)
        self.assertEqual(blocks[0].kind, "code")
        self.assertEqual(blocks[0].text, "print(1)\nprint(2)")

    def test_paragraph_merges_lines(self):
        blocks = parse_markdown("第一行\n第二行\n\n新段落")
        paras = [b for b in blocks if b.kind == "para"]
        self.assertEqual(len(paras), 2)
        self.assertEqual(paras[0].runs[0].text, "第一行 第二行")

    def test_inline_runs_kept_in_blocks(self):
        blocks = parse_markdown("普通 **粗体** 文字")
        self.assertEqual([r.style for r in blocks[0].runs], ["text", "bold", "text"])


if __name__ == "__main__":
    unittest.main()
