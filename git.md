# ==============================================
# Git 命令大全（代码格式）
# ==============================================

# 1. 初始化和克隆
git init                            # 初始化本地仓库
git clone <repo-url>                # 克隆远程仓库
git clone <repo-url> <dir-name>     # 克隆到指定目录
git clone --depth=1 <repo-url>      # 浅克隆（只拉取最新提交）

# 2. 配置Git
git config --global user.name "Your Name"       # 设置全局用户名
git config --global user.email "your@email.com" # 设置全局邮箱
git config --global core.editor "vim"           # 设置默认编辑器
git config --list                               # 查看所有配置
git config --global alias.co checkout           # 设置别名（git co = git checkout）

# 3. 基本操作
git status                      # 查看仓库状态
git add <file>                  # 添加文件到暂存区
git add .                       # 添加所有变更到暂存区
git commit -m "message"         # 提交变更
git commit --amend              # 修改最近一次提交
git reset <file>                # 从暂存区移除文件
git reset --hard                # 丢弃所有未提交变更（慎用！）
git restore <file>              # 撤销工作区修改（Git 2.23+）
git restore --staged <file>      # 从暂存区移出文件

# 4. 分支管理
git branch                      # 查看本地分支
git branch -a                   # 查看所有分支（包括远程）
git branch <branch-name>        # 创建新分支
git checkout <branch-name>      # 切换分支
git checkout -b <branch-name>   # 创建并切换分支
git merge <branch-name>         # 合并分支
git rebase <branch-name>        # 变基
git branch -d <branch-name>     # 删除本地分支
git branch -D <branch-name>     # 强制删除未合并分支
git push origin --delete <branch-name>  # 删除远程分支

# 5. 远程仓库操作
git remote -v                   # 查看远程仓库
git remote add origin <repo-url> # 添加远程仓库
git remote remove origin        # 移除远程仓库
git fetch                       # 拉取远程变更（不合并）
git pull                        # 拉取并合并远程变更
git pull --rebase               # 拉取并变基
git push                        # 推送本地变更
git push -u origin <branch>     # 首次推送并设置upstream
git push --force                # 强制推送（慎用！）

# 6. 查看提交历史
git log                         # 查看提交历史
git log --oneline               # 简洁模式查看
git log --graph                 # 图形化查看
git log -p                      # 查看详细变更
git log --author="name"         # 按作者筛选
git log --since="1 week ago"    # 按时间筛选
git show <commit-id>            # 查看某次提交详情

# 7. 撤销与回退
git reset --soft HEAD~1         # 撤销commit，保留修改
git reset --hard HEAD~1         # 彻底丢弃commit和修改
git revert <commit-id>          # 撤销某次提交（生成新commit）
git cherry-pick <commit-id>     # 复制某次提交
git stash                       # 暂存当前修改
git stash pop                   # 恢复暂存修改
git stash list                  # 查看所有暂存记录
git stash drop                  # 删除最近暂存

# 8. 标签管理
git tag                         # 查看所有标签
git tag v1.0.0                  # 创建轻量标签
git tag -a v1.0.0 -m "Release"  # 创建带注释标签
git push origin v1.0.0          # 推送标签
git push origin --tags          # 推送所有标签
git tag -d v1.0.0               # 删除本地标签
git push origin --delete v1.0.0 # 删除远程标签

# 9. 高级操作
git rebase -i HEAD~3            # 交互式变基（修改最近3次提交）
git bisect start                # 二分查找bug提交
git submodule add <repo-url>    # 添加子模块
git blame <file>                # 查看文件修改历史（逐行）
git reflog                      # 查看所有操作记录（可恢复误删）

# ==============================================
# 常用工作流示例
# ==============================================

# 日常开发流程
git checkout -b feature/new-feature  # 创建并切换分支
git add .                           # 添加修改
git commit -m "Add new feature"     # 提交
git push -u origin feature/new-feature # 推送到远程

# 合并分支
git checkout main
git pull origin main               # 先更新main分支
git merge feature/new-feature      # 合并特性分支
git push origin main               # 推送合并结果

# 解决冲突后继续rebase
git rebase --continue

# 撤销错误的push
git reset --hard HEAD~1            # 本地回退
git push --force origin main       # 强制推送（慎用）