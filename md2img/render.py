"""渲染引擎：主题 → 卡片图片。

两阶段：先把每个块换算成带绝对坐标的绘制操作并精确计算总高，再统一绘制。
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .blocks import Run, parse_markdown

FONT_CANDIDATES = {
    "text": ["C:/Windows/Fonts/msyh.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
             "/System/Library/Fonts/PingFang.ttc"],
    "bold": ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "mono": ["C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
}


@dataclass
class Theme:
    name: str
    bg: str
    paper: str
    text: str
    muted: str
    accent: str
    code_bg: str
    code_text: str


THEMES = {
    "light": Theme("light", bg="#E8E4D8", paper="#FFFFFF", text="#2B2B2B",
                   muted="#8A8578", accent="#1F6E5C", code_bg="#F4F2EA", code_text="#8C4A3C"),
    "dark": Theme("dark", bg="#22262B", paper="#2B3138", text="#E6E2D8",
                  muted="#9AA0A6", accent="#5FB89A", code_bg="#1E2329", code_text="#E0A075"),
    "sepia": Theme("sepia", bg="#D8CFBC", paper="#F7F1E3", text="#4A3B2A",
                   muted="#A0907A", accent="#B0563A", code_bg="#EFE6D2", code_text="#7A5230"),
}


def _find_font(candidates: list[str], size: int):
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


class Renderer:
    def __init__(self, theme: str = "light", width: int = 720, base_size: int = 24):
        if theme not in THEMES:
            raise ValueError(f"未知主题 {theme!r}（可选：{'/'.join(THEMES)}）")
        self.t = THEMES[theme]
        self.width = width
        self.base = base_size
        self.pad = width // 10
        self.f = {
            "h1": _find_font(FONT_CANDIDATES["bold"], int(base_size * 1.7)),
            "h2": _find_font(FONT_CANDIDATES["bold"], int(base_size * 1.35)),
            "h3": _find_font(FONT_CANDIDATES["bold"], int(base_size * 1.15)),
            "text": _find_font(FONT_CANDIDATES["text"], base_size),
            "bold": _find_font(FONT_CANDIDATES["bold"], base_size),
            "mono": _find_font(FONT_CANDIDATES["mono"], int(base_size * 0.9)),
            "small": _find_font(FONT_CANDIDATES["text"], int(base_size * 0.85)),
        }

    # ---------- 行内折行 ----------
    def _style_of(self, run: Run):
        key = "bold" if run.style == "bold" else ("mono" if run.style == "code" else "text")
        color = self.t.code_text if run.style == "code" else self.t.text
        return self.f[key], color

    def _wrap_runs(self, runs: list[Run], max_w: int) -> list[list[tuple[str, str, str]]]:
        """折行 → 每行是 (text, font_key, color) 列表。按字符计量，CJK 友好。"""
        lines: list[list[tuple[str, str, str]]] = []
        cur: list[tuple[str, str, str]] = []
        cur_w = 0.0
        for run in runs:
            font, color = self._style_of(run)
            buffer = ""
            for ch in run.text:
                w = font.getlength(ch)
                if cur_w + w > max_w and (cur or buffer):
                    if buffer.strip():
                        cur.append((buffer, self._key(run), color))
                    lines.append(cur)
                    cur, cur_w = [], 0.0
                    buffer = "" if ch == " " else ch
                    cur_w = 0.0 if ch == " " else w
                else:
                    buffer += ch
                    cur_w += w
            if buffer:
                cur.append((buffer, self._key(run), color))
        if cur:
            lines.append(cur)
        return lines or [[]]

    def _key(self, run: Run) -> str:
        return "bold" if run.style == "bold" else ("mono" if run.style == "code" else "text")

    @staticmethod
    def _wrap_mono(text: str, font, max_w: int) -> list[str]:
        """等宽行折行（代码块用）；缩进空格保留在行首。"""
        if not text:
            return [""]
        out: list[str] = []
        cur = ""
        cur_w = 0.0
        for ch in text:
            w = font.getlength(ch)
            if cur_w + w > max_w and cur:
                out.append(cur)
                cur = ch.lstrip() if cur and ch == " " else ch
                cur_w = font.getlength(cur)
            else:
                cur += ch
                cur_w += w
        if cur or not out:
            out.append(cur)
        return out

    # ---------- 排版 ----------
    def _layout(self, md: str, footer: str):
        """返回 (ops, total_height)。op = (kind, dict)。"""
        blocks = parse_markdown(md)
        content_w = self.width - self.pad * 2
        ops: list[tuple[str, dict]] = []
        y = self.pad
        gap = int(self.base * 0.45)

        for b in blocks:
            if b.kind == "heading":
                key = "h1" if b.level == 1 else ("h2" if b.level == 2 else "h3")
                font = self.f[key]
                lines = self._wrap_runs(b.runs, content_w - (int(self.base * 0.7) if b.level == 1 else 0))
                lh = int(font.size * 1.45)
                y += gap
                ops.append(("heading", {"level": b.level, "lines": lines, "font": font,
                                        "lh": lh, "y": y}))
                y += lh * len(lines) + gap * 2
            elif b.kind == "hr":
                y += gap
                ops.append(("hr", {"y": y}))
                y += gap * 2
            elif b.kind == "code":
                # 代码行也按纸面宽度折行，避免长命令溢出
                mono_w = content_w - int(self.base * 1.1)
                wrapped: list[str] = []
                for raw in (b.text.split("\n") or [""]):
                    for line in self._wrap_mono(raw, self.f["mono"], mono_w):
                        wrapped.append(line)
                lh = int(self.f["mono"].size * 1.6)
                bh = lh * len(wrapped) + int(self.base * 0.9)
                ops.append(("code", {"lines": wrapped, "lh": lh, "y": y, "bh": bh}))
                y += bh + gap * 2
            elif b.kind == "quote":
                lines = self._wrap_runs([Run(b.text)], content_w - int(self.base * 1.4))
                lh = int(self.f["text"].size * 1.6)
                qh = lh * len(lines) + int(self.base * 0.8)
                ops.append(("quote", {"lines": lines, "lh": lh, "y": y, "qh": qh}))
                y += qh + gap * 2
            else:  # para / bullet / olist
                prefix = "•  " if b.kind == "bullet" else (f"{b.marker}.  " if b.kind == "olist" else "")
                indent = int(self.f["text"].size * 1.9) if prefix else 0
                lines = self._wrap_runs(b.runs, content_w - indent)
                lh = int(self.f["text"].size * 1.6)
                ops.append(("para", {"prefix": prefix, "lines": lines, "lh": lh,
                                     "indent": indent, "y": y}))
                y += lh * len(lines) + gap

        total = y + self.pad
        if footer:
            footer_y = y + int(self.base * 0.6)
            total = footer_y + int(self.base * 2.0) + self.pad // 2
            ops.append(("footer", {"y": footer_y, "text": footer}))
        return ops, total

    def render(self, md: str, footer: str = "") -> Image.Image:
        ops, total = self._layout(md, footer)
        img = Image.new("RGB", (self.width, total), self.t.bg)
        draw = ImageDraw.Draw(img)
        m = self.pad // 3
        draw.rounded_rectangle([m, m, self.width - m, total - m],
                               radius=int(self.base * 0.8), fill=self.t.paper)
        x0 = self.pad
        content_w = self.width - self.pad * 2

        for kind, o in ops:
            if kind == "heading":
                font, lh, y = o["font"], o["lh"], o["y"]
                if o["level"] == 1:
                    draw.rectangle([x0, y + lh * 0.2, x0 + int(self.base * 0.22),
                                    y + lh * 0.85], fill=self.t.accent)
                color = self.t.accent if o["level"] == 1 else self.t.text
                tx = x0 + (int(self.base * 0.7) if o["level"] == 1 else 0)
                for line in o["lines"]:
                    x = tx
                    for text, key, color_run in line:
                        f = self.f[key]
                        draw.text((x, y), text, font=f, fill=color)
                        x += f.getlength(text)
                    y += lh
            elif kind == "hr":
                draw.line([x0, o["y"], x0 + content_w, o["y"]], fill=self.t.muted, width=1)
            elif kind == "code":
                draw.rounded_rectangle([x0, o["y"], x0 + content_w, o["y"] + o["bh"]],
                                       radius=int(self.base * 0.4), fill=self.t.code_bg)
                ty = o["y"] + int(self.base * 0.45)
                for line in o["lines"]:
                    draw.text((x0 + int(self.base * 0.5), ty), line,
                              font=self.f["mono"], fill=self.t.code_text)
                    ty += o["lh"]
            elif kind == "quote":
                draw.rectangle([x0, o["y"] + int(self.base * 0.2), x0 + int(self.base * 0.16),
                                o["y"] + o["qh"] - int(self.base * 0.2)], fill=self.t.accent)
                ty = o["y"] + int(self.base * 0.4)
                for line in o["lines"]:
                    x = x0 + int(self.base * 0.8)
                    for text, key, color in line:
                        f = self.f["text"]
                        draw.text((x, ty), text, font=f, fill=self.t.muted)
                        x += f.getlength(text)
                    ty += o["lh"]
            elif kind == "para":
                y = o["y"]
                for line in o["lines"]:
                    x = x0 + o["indent"]
                    if o["prefix"]:
                        draw.text((x0, y), o["prefix"], font=self.f["text"], fill=self.t.accent)
                    for text, key, color in line:
                        f = self.f[key]
                        draw.text((x, y), text, font=f, fill=color)
                        x += f.getlength(text)
                    y += o["lh"]
            elif kind == "footer":
                draw.line([x0, o["y"] - int(self.base * 0.5), x0 + content_w, o["y"] - int(self.base * 0.5)],
                          fill=self.t.muted, width=1)
                fw = self.f["small"].getlength(o["text"])
                draw.text(((self.width - fw) / 2, o["y"]), o["text"],
                          font=self.f["small"], fill=self.t.muted)
        return img


def render(md: str, theme: str = "light", width: int = 720,
           base_size: int = 24, footer: str = "") -> Image.Image:
    """便捷入口：Markdown 文本 → 卡片图。"""
    return Renderer(theme=theme, width=width, base_size=base_size).render(md, footer=footer)


def render_file(path: Path | str, **kw) -> Image.Image:
    return render(Path(path).read_text(encoding="utf-8-sig"), **kw)
