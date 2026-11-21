"""命令行入口：``python -m md2img`` 或安装后 ``md2img``。

用法：
    python -m md2img card.md -o card.png
    python -m md2img card.md -o card.png --theme dark --width 760 --footer "@chiyuki"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .render import THEMES, render

SAMPLE = """# 标题

**加粗文字** 与 `行内代码`，普通正文可以折行。

## 列表
- 第一条
- 第二条

> 一句值得引用的话

```python
print("hello")
```
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="md2img", description="Markdown 转分享卡片图")
    ap.add_argument("--version", action="version", version=f"md2img {__version__}")
    ap.add_argument("input", nargs="?", help="Markdown 文件；缺省时打印示例到 stdout")
    ap.add_argument("-o", "--output", help="输出 PNG 路径")
    ap.add_argument("--theme", default="light", choices=sorted(THEMES), help="主题（默认 light）")
    ap.add_argument("--width", type=int, default=720, help="卡片宽度（默认 720）")
    ap.add_argument("--size", type=int, default=24, help="正文字号（默认 24）")
    ap.add_argument("--footer", default="", help="页脚文字，如 @yourname")
    args = ap.parse_args(argv)

    if not args.input:
        print(SAMPLE)
        return 0
    src = Path(args.input)
    if not src.exists():
        print(f"错误：文件不存在 {src}", file=sys.stderr)
        return 1
    md = src.read_text(encoding="utf-8-sig")
    img = render(md, theme=args.theme, width=args.width, base_size=args.size,
                 footer=args.footer)
    out = Path(args.output) if args.output else src.with_suffix(".png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"已生成卡片 {img.size[0]}×{img.size[1]} → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
