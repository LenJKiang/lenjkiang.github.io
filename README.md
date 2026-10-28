# 林李泽强 Ze-Qiang Linli 个人学术网站

V0.4，2026-10-28。五项主导航：首页、研究、教学、团队与招生、关于我。中英页面共享数据；首页展示5篇代表作，研究页以连续列表展示22篇论文，按年份降序、同年第一/共同一作、通讯作者、其他作者排序，不显示筛选框或研究方向标签。页面不显示内部核验、版权审批或本地预览提示，相关记录仍保留在私人工作区。用户已授权首次推送和GitHub Pages部署；二进制资料仍单独审批。

2026-10-28全站文字校对已完成：中英文同步润色、统一CSCD及修正标点，详细记录见 `workspace/reports/copyedit-20261028.md`。

## 本地预览

在项目根目录运行：

```powershell
python scripts/build_site.py
python scripts/preview.py --local-resources --port 8001
```

打开 http://127.0.0.1:8001/ 或 http://127.0.0.1:8001/en/ 。按 Ctrl+C 停止；如果已经构建，只需第二条。

`--local-resources` 会在私人工作区生成并预览：个人照片、20篇论文 PDF（另两篇按本人要求仅展示发表信息）、概率论第一章5份和第二章2份 PDF；教学总览和课程详情均可访问课件。PPT/PPTX 不进入网站。预览内容位于 `workspace/preview-site/`，带 noindex，与可部署的 `dist/` 分开。此开关仅供本机测试，不记录公开传播批准。两篇中文论文无需PDF，不显示下载或索取入口，也不列为待补PDF；其DOI尚未核实，不生成虚构链接。其余20篇已从所供论文核对DOI。

普通 `python scripts/preview.py` 预览 `dist/`，其中只含已核验的元数据和获准公开的资源。2026-10-28用户授权同步部署照片、论文及课件；当前公开清单包含个人照片、7份概率论PDF和2篇明确采用CC BY-NC-ND 4.0的论文PDF。其余18份论文的现有出版社版本尚缺公开托管依据，继续提供DOI及索取入口，待补作者接受稿或具体许可。两篇本人指定无需PDF的中文论文不在这18份中。

## 日常维护

- 论文唯一数据：`data/publications.yml`。22 条来自用户提供并确认的清单，保留作者角色；正式 PDF/出版商题名优先于清单中的早期题名。不从文件名推断分区、作者顺位或年份。代表作由 `selected: true` 和 `selected_order: 1–5` 控制；当前顺序为Communications Biology、NeuroImage、PNP 2025、PNP 2022、Cerebral Cortex。
- 项目与荣誉：`data/academic.yml`。7项科研、3项教研、14项本人荣誉、11条学生指导成果与5项学术服务，保留来源日期并区分获奖对象。
- 课程唯一数据：`data/courses.yml`。当前概率论第一章5份、第二章2份PDF，按章节分表；本地映射在私人预览清单中。
- 个人及研究数据：`data/profile.yml`、`data/research.yml`；公开链接：`data/links.yml`。`profile.yml` 的 `bio_zh/en` 控制首页个人简介（可用星号包围期刊名以斜体显示），`summary_zh/en` 控制研究页概述和首页SEO摘要，`research_overview_zh/en` 控制首页及研究页的单段研究介绍，`teaching_overview_zh/en` 控制教学概述，`about_intro_zh/en` 控制关于我的概述；`team_purpose_zh/en`、`team_members_zh/en`、`team_recruitment_zh/en` 控制团队页。课程对象和教材使用 `courses.yml` 的 `audience_zh/en`、`textbook_zh/en`。修改中文后应同步英文。
- 不手工维护生成的 HTML/QMD；修改共享数据后重新构建。`website/zh/`、`website/en/`和`dist/`均为生成输出，不提交；构建器会自动创建中英页面，权威内容为`data/`，模板与样式位于`scripts/`和`website/shared/`。
- 收件区：`workspace/inbox/`。默认私人，不进入 Git 或部署输出。
- 测试文件白名单：`workspace/review/local-preview.yml`。逐文件 SHA-256；源文件变化后拒绝沿用旧映射。
- 21篇论文的规范命名副本：`workspace/working/named-papers/`。原件不改名、不移动；对应表见 `workspace/review/filename-mapping.yml`。
- 真正允许公开的文件才通过 `scripts/review_resource.py` 写入 `public/`、公开哈希白名单和资源数据库。先核验版本、许可、禁发期及必要声明，再由用户明确批准。测试权限不代替公开权限。

新增论文或课件：放入收件区 → `python scripts/scan_resources.py --type papers` 或 `--type teaching` → 核对候选元数据/版本/许可 → 更新数据 → 构建和测试。不要把所有收件资料直接拖到 GitHub。

本项目使用 RStudio 内置 Quarto 1.9.38，Python 依赖见 requirements.txt。无需重复安装 Quarto；若脚本找不到，设置当前终端的 QUARTO_PATH 指向实际程序。Windows 中文路径兼容逻辑保留在项目内，不修改 RStudio。

## 测试

```powershell
python scripts/validate_content.py
python scripts/build_site.py
python -m unittest discover -s tests -v
python scripts/test_fixture_build.py
python scripts/validate_site.py
python scripts/prepublish.py
python scripts/prepublish.py --staged
```

测试须在实际构建后执行。可运行 `python scripts/check_revision.py` 汇总当前检查日志；旧入口 run_checks.py 已转到同一套检查，避免重写历史报告。真实资源本机预览另由 `build_local_preview.py` 校验；浏览器检查脚本为 `browser_check.cjs`，可用已有 Playwright 和 Edge，不需下载新浏览器。浏览器读写目录均在私人工作区。

项目子路径：先 `python scripts/build_site.py --base-path /Academic_Website/`，再用匹配的 `preview.py --base-path /Academic_Website/`；检查后用默认构建恢复根路径。私人资源预览也需同一 base_path。

## GitHub

仓库：`https://github.com/LenJKiang/lenjkiang.github.io`；网站：`https://lenjkiang.github.io/`。名称、根路径及正式网址已写入 `config/site.yml`。本地远程origin已连接仓库；2026-10-28获用户授权首次发布。

`main`上的推送会触发 `.github/workflows/pages.yml`：验证数据、生成双语页面、构建和测试后部署通过白名单检查的`dist/`；Pull Request仅构建和测试。GitHub Pages发布来源设为GitHub Actions。实际首次发布结果以GitHub Actions运行状态和网站访问验证为准。

每次发布前仍需检查源码暂存树、PDF分享许可、照片和教学资料公开范围。`data/resources.yml`和`config/public-assets.yml`保存当前10个文件的哈希和审批依据；公开照片和PDF位于`public/`。私人预览中的其余18份论文PDF及全部PPT/PPTX保留在`workspace/`。项目Git钩子只做检查，不会自动暂存或提交。

本次变更与测试汇总：`workspace/reports/revision_v04.md`。V0.2、V0.3和初次实施报告保留为历史记录。长期规则见 AGENTS.md；首次规格见 CODEX_SPEC.md。
