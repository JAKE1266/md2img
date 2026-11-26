# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式,
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.1] - 2026-11-26

### 修复
- CI 安装声明的 Pillow 依赖,并固定 Ubuntu 24.04 以支持 Python 3.9
- CI 构建 wheel/sdist、检查元数据,并在干净虚拟环境中安装真实 wheel
- Windows cp1252 环境下中文 CLI 输出改为 UTF-8
- Pillow 最低版本提升至 10.1,确保默认字体支持字号参数

### 变更
- Python 最低版本统一为 3.9,发布元数据迁移到 SPDX 许可证表达式
- README 修正依赖徽章与安装命令,新增已安装 wheel 冒烟测试

## [0.1.0] - 2026-11-21

### 新增
- 核心功能实现(Markdown 解析 + Pillow 渲染)
- CLI 命令行入口
- 18 个单元测试
- GitHub Actions 三系统 × 多版本 CI
- 中文 README 与 MIT 许可证

### 变更
- 补齐徽章、项目结构与本日志,与其他仓库文档标准统一
