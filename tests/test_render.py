import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from md2img.render import THEMES, Renderer, render

MD = """# 分享卡片标题

这是 **加粗正文**，包含 `inline code`，还有一段足够长的文字用来验证自动折行是否正常工作，直到超过一行宽度为止。

- 第一个要点
- 第二个要点

> 引用：少即是多。

```python
print("hello card")
```

---

## 小节
结尾正文。
"""


class TestRender(unittest.TestCase):
    def test_size_and_background(self):
        img = render(MD, theme="light", width=720)
        self.assertEqual(img.size[0], 720)
        # 卡片外背景色 = 主题 bg
        self.assertEqual(img.getpixel((2, 2)), (232, 228, 216))
        # 卡片内部应是纸面色
        self.assertEqual(img.getpixel((360, 40)), (255, 255, 255))

    def test_all_themes_render(self):
        for name in THEMES:
            img = render("# 标题\n\n正文。", theme=name)
            self.assertEqual(img.size[0], 720)

    def test_width_respected(self):
        self.assertEqual(render(MD, width=560).size[0], 560)

    def test_long_text_wraps_within_margins(self):
        long_para = "这" * 120
        img = render(long_para)
        # 不应越界：卡片纸面左右留白处仍是纸面色（取样边缘）
        w, h = img.size
        edge = img.getpixel((w // 2, h - 10))
        self.assertNotEqual(edge, (0, 0, 0))

    def test_invalid_theme(self):
        with self.assertRaises(ValueError):
            render("x", theme="neon")

    def test_content_below_footer_visible(self):
        img = render("正文一句", footer="@someone")
        self.assertGreater(img.size[1], 200)


class TestCli(unittest.TestCase):
    def test_cli_generates_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "card.md"
            src.write_text(MD, encoding="utf-8")
            dst = Path(tmp) / "card.png"
            r = subprocess.run([sys.executable, "-m", "md2img", str(src), "-o", str(dst),
                                "--theme", "dark", "--footer", "@me"],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("已生成卡片", r.stdout)
            self.assertTrue(dst.exists())
            with Image.open(dst) as img:
                self.assertEqual(img.size[0], 720)

    def test_cli_missing_file(self):
        r = subprocess.run([sys.executable, "-m", "md2img", "nope.md"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 1)

    def test_cli_utf8_output_under_legacy_windows_encoding(self):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "cp1252"
        env.pop("PYTHONUTF8", None)

        result = subprocess.run([sys.executable, "-m", "md2img"], capture_output=True, env=env)

        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        self.assertIn("加粗文字", result.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
