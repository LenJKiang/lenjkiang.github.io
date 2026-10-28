# GitHub 仓库与后续准备

仓库：https://github.com/LenJKiang/lenjkiang.github.io.git 。2026-10-28已验证所有者为LenJKiang，当前账号有管理和写入权限。用户已授权推送、部署及同步照片、论文和课件；本地已连接origin，Pages使用GitHub Actions，正式网址为https://lenjkiang.github.io/ 。仅发布已通过版本、许可及哈希审核的资源。

未来用户站地址为 https://lenjkiang.github.io/ ，使用根路径 `/`。本地预览仍使用 `python scripts/preview.py --local-resources --port 8001`。

后续维护：

1. 确定要分享的照片、论文和教学PDF，核对版本、许可、必要声明和逐文件SHA-256审批。
2. 检查 `data/`、`public/`、Git暂存内容及 `dist/`，执行README中的构建、测试和发布前检查。
3. 检查远程最新提交，提交经过核验的源码并正常推送，不得强制覆盖远程内容。
4. Settings → Pages使用GitHub Actions。`main`分支每次推送自动构建、验证和部署，Pull Request不部署；首次发布结果须检查Actions实际运行状态和正式网站。

`workspace/` 和 `workspace/preview-site/` 为私人工作区，不能上传。当前页面省略内部审核说明，不改变文件权限；本地PDF预览清单不构成公开传播许可。Actions只使用经过公开白名单验证的 `dist/`。
