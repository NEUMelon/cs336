# CS336（Spring 2026）中文学习笔记

Stanford CS336《从零构建语言模型》全部 17 讲的中文详解笔记（HTML）。
每一讲先从第一性原理提出核心问题，再沿官方讲义展开推导，最后给出要点和自测题。

- 在线阅读（GitHub Pages）：<https://neumelon.github.io/cs336/>
- 本地：打开 `index.html` 查看目录，或直接打开 `lectures/lecture_XX.html`。
- 内容依据官方讲义 <https://github.com/stanford-cs336/lectures>（`lecture_XX.py` / `lecture_XX.pdf`）整理；
  标注为“第一性原理”“补充”的部分是笔记作者的推导和解释。

## 目录结构

- `src/lecture_XX.html`：每讲的内容片段（开头的 `<!--meta ... -->` 是标题等元信息）
- `src/style.css`：共享样式
- `build.py`：生成 `lectures/*.html`、`index.html`，以及用于发布的单页版本 `site/app.html`
- `lectures/`、`index.html`：生成的页面，可直接在浏览器中打开

修改 `src/` 后运行：

    python3 build.py
