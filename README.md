# md2img

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-18%20passing-success)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

Markdown 转分享卡片图 —— 用一条命令把一段 Markdown 变成排版精致的分享卡片（金句卡 / 知识卡 / 观点速递）。

- **块级元素**：一/二/三级标题、段落、无序与有序列表、引用、代码块、分隔线
- **行内元素**：`**粗体**` 与 `` `行内代码` ``（等宽字体 + 强调色）
- **三套主题**：`light` 米白纸面 / `dark` 暗夜墨绿 / `sepia` 复古牛皮纸
- **中文排版**：按字符计量折行（CJK 友好），代码块同样折行不越界
- **卡片细节**：圆角纸面 + 背景衬托 + 标题强调竖条 + 引用竖线 + 页脚署名
- **跨平台字体**：微软雅黑 / 黑体 / DejaVu / PingFang 回退链

依赖 Pillow，Python ≥ 3.8。

## 安装

```bash
pip install Pillow
pip install .        # 获得 md2img 命令
python -m md2img     # 无参数时打印示例 Markdown
```

## 真实运行示例

```console
$ python -m md2img demo/card.md -o card.png --theme dark --width 760 --footer "@open-source"
已生成卡片 760×870 → card.png
```

实际渲染效果（同一 Markdown，light 与 dark 两套主题）：

- light：米白背景 + 白色纸面 + 墨绿标题竖条 + 竖线引用
- dark：深灰背景 + 暗面板 + 青绿强调 + 橙色等宽代码

## 参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `-o` | 输出 PNG 路径 | 与输入同名 `.png` |
| `--theme` | `light` / `dark` / `sepia` | light |
| `--width` | 卡片宽度 | 720 |
| `--size` | 正文字号 | 24 |
| `--footer` | 页脚署名 | 无 |

## 作为库使用

```python
from md2img import render

card = render("# 你好\n\n**Markdown** 转卡片。", theme="sepia", footer="@me")
card.save("hello.png")
```

## 设计取舍

- **两阶段渲染**：先把每个块换算成带绝对坐标的绘制操作并精确算总高，再统一绘制——不会出现内容越界或底部留白忽大忽小
- **逐字符计量折行**：中文没有空格，`font.getlength` 逐字符累加比按空格 split 更可靠
- **只支持常用 Markdown 子集**：分享卡片用不到表格/图片/嵌套列表，克制功能换取稳定排版

## 运行测试

```bash
python -m unittest discover -s tests
# Ran 18 tests ... OK
```


## 📁 项目结构

```
md2img/
├── LICENSE
├── demo/
├── md2img/
├── pyproject.toml
├── tests/
└── README.md
```

## License

MIT
