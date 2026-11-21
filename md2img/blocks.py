"""极简 Markdown 块解析：标题 / 列表 / 引用 / 代码块 / 分隔线 / 段落。

只覆盖分享卡片常见的块级元素与行内元素（**粗体**、`代码`），
完整 Markdown 规范不在目标范围内。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

INLINE_RE = re.compile(r"(\*\*.+?\*\*|`.+?`)")
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")
_UL_RE = re.compile(r"^[-*]\s+(.*)$")
_OL_RE = re.compile(r"^(\d+)[.、]\s*(.*)$")


@dataclass
class Run:
    """一段同样式文本：style ∈ text / bold / code。"""

    text: str
    style: str = "text"


@dataclass
class Block:
    kind: str                 # heading / para / bullet / olist / quote / code / hr
    level: int = 0            # heading 层级 1~3
    runs: list[Run] = field(default_factory=list)
    text: str = ""            # 纯文本（quote 整行 / code 整段 / hr 忽略）
    marker: str = ""          # 有序列表序号


def parse_inline(text: str) -> list[Run]:
    """解析 **粗体** 与 `代码`，其余为普通文本。"""
    runs: list[Run] = []
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            runs.append(Run(part[2:-2], "bold"))
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            runs.append(Run(part[1:-1], "code"))
        else:
            runs.append(Run(part, "text"))
    return runs or [Run(text)]


def strip_inline(text: str) -> str:
    return "".join(r.text for r in parse_inline(text))


def parse_markdown(md: str) -> list[Block]:
    blocks: list[Block] = []
    lines = md.replace("\r\n", "\n").split("\n")
    i = 0
    para: list[str] = []

    def flush_para():
        if para:
            blocks.append(Block("para", runs=parse_inline(" ".join(para).strip())))
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para()
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # 跳过收尾 ```
            blocks.append(Block("code", text="\n".join(code).rstrip()))
            continue

        if not stripped:
            flush_para()
            i += 1
            continue

        m = _HEADING_RE.match(stripped)
        if m:
            flush_para()
            blocks.append(Block("heading", level=len(m.group(1)),
                                runs=parse_inline(m.group(2).strip()),
                                text=strip_inline(m.group(2).strip())))
            i += 1
            continue

        if stripped in ("---", "***", "___"):
            flush_para()
            blocks.append(Block("hr"))
            i += 1
            continue

        m = _UL_RE.match(stripped)
        if m:
            flush_para()
            blocks.append(Block("bullet", runs=parse_inline(m.group(1))))
            i += 1
            continue

        m = _OL_RE.match(stripped)
        if m:
            flush_para()
            blocks.append(Block("olist", runs=parse_inline(m.group(2)), marker=m.group(1)))
            i += 1
            continue

        if stripped.startswith(">"):
            flush_para()
            blocks.append(Block("quote", text=strip_inline(stripped.lstrip(">").strip())))
            i += 1
            continue

        para.append(stripped)
        i += 1

    flush_para()
    return blocks
