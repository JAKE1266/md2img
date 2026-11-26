import os
import subprocess
import sys
import tempfile
from importlib.metadata import distribution
from pathlib import Path

from PIL import Image

import md2img


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    module_path = Path(md2img.__file__).resolve()
    if module_path == (ROOT / "md2img" / "__init__.py").resolve():
        raise RuntimeError(f"md2img 仍从源码目录导入：{module_path}")

    package = distribution("md2img")
    if package.version != "0.1.1":
        raise RuntimeError(f"版本不符：{package.version}")
    requirements = package.requires or []
    if not any(req.lower().replace(" ", "").startswith("pillow>=10.1") for req in requirements):
        raise RuntimeError(f"Pillow 依赖元数据缺失：{requirements}")

    scripts_dir = Path(sys.executable).parent
    console = scripts_dir / ("md2img.exe" if os.name == "nt" else "md2img")
    if not console.exists():
        raise RuntimeError(f"控制台脚本不存在：{console}")

    version = subprocess.run([str(console), "--version"], capture_output=True)
    if version.returncode != 0 or b"md2img 0.1.1" not in version.stdout:
        raise RuntimeError(f"控制台脚本版本检查失败：{version.stderr!r}")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"
    env.pop("PYTHONUTF8", None)

    sample = subprocess.run([sys.executable, "-m", "md2img"], capture_output=True, env=env)
    if sample.returncode != 0 or "加粗文字".encode("utf-8") not in sample.stdout:
        raise RuntimeError(f"中文输出检查失败：{sample.stderr!r}")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        source = work / "card.md"
        output = work / "card.png"
        source.write_text("# 已安装 wheel\n\n**中文内容** 与 `行内代码`。", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "md2img", str(source), "-o", str(output),
             "--theme", "dark", "--width", "760", "--footer", "@open-source"],
            cwd=work,
            capture_output=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(f"CLI 渲染失败：{result.stderr!r}")
        if "已生成卡片".encode("utf-8") not in result.stdout:
            raise RuntimeError("CLI 中文成功信息不是 UTF-8")
        with Image.open(output) as image:
            if image.format != "PNG" or image.size[0] != 760:
                raise RuntimeError(f"输出图片不符：{image.format} {image.size}")

        card = md2img.render("# 库调用\n\n**冒烟测试**。", theme="sepia", width=640)
        card.save(work / "library.png")
        with Image.open(work / "library.png") as image:
            if image.format != "PNG" or image.size[0] != 640:
                raise RuntimeError(f"库调用输出不符：{image.format} {image.size}")

    print("Installed wheel smoke test passed")


if __name__ == "__main__":
    main()
