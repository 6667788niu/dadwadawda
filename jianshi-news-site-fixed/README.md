# 见势 · 每日社会认知情报站

一个可部署到 GitHub Pages 的中文新闻网站：每天早上约 7:20（北京时间）通过 GitHub Actions 自动抓取近 7 天的新闻索引、按权威来源域名过滤、按主题与时间计算参考重要度，并可选用 OpenAI API 生成谨慎的大白话解读。

## 部署（约 10 分钟）

1. 登录 GitHub，新建一个 **Public** 仓库，例如 `jianshi-news`，默认分支使用 `main`。
2. 将本项目中的 **全部文件和文件夹** 上传到仓库根目录（包含 `.github/workflows/daily.yml`）。可以先在电脑解压 ZIP，再通过 GitHub 网页上传文件；注意隐藏的 `.github` 文件夹也必须上传。
3. 仓库 `Settings → Pages → Build and deployment → Source` 选择 **GitHub Actions**。
4. 如果要启用 AI 解读：在 `Settings → Secrets and variables → Actions → New repository secret` 新增 `OPENAI_API_KEY`，填入你自己的 OpenAI API 密钥。**不要把密钥写进网页或代码文件。** API 可能产生费用。未配置密钥时仍能展示标题和来源，但不会生成真正的 AI 解读。
5. 打开仓库 `Actions → Daily news digest → Run workflow`，等待工作流成功。
6. 打开 `Settings → Pages` 查看发布地址，一般为 `https://你的用户名.github.io/jianshi-news/`。可将网址添加到手机桌面。

## 本地预览

```bash
python -m pip install -r requirements.txt
python build.py
python -m http.server 8000 --directory site
```

打开 http://localhost:8000 。如果网络无法访问 Google News RSS，生成结果可能为空；检查命令行错误提示。

## 必须知道的限制

- 数据入口为 **Google News RSS 聚合索引**，不是直接调用政府部门的新闻 API；只筛选索引中标记的指定域名来源。点击链接可能先进入聚合跳转页。
- AI **只看到新闻标题和来源**，不会自动读取或核实新闻全文。所有分析均应视为辅助理解，而不是经证实的独家消息。
- 重要度分数是基于栏目权重和发布时间的**规则评分**，不是人工编辑逐条审定的权威排行。
- GitHub Actions 定时任务可能延迟或偶尔跳过；可在 Actions 手动运行。Google News 在部分地区可能无法访问。
- 这是可运行的初版，不包含用户账号、数据库、付费订阅、全文检索或可靠的跨媒体事实核查。
- 如果需要更高质量的分析，可升级为：直连官方 RSS / API、抓取正文、交叉来源验证、人工审核、明确的评分标准。
