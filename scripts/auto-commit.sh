#!/bin/bash
# 文档自动提交脚本

cd /root/.openclaw/workspace/AI-Engineering-Docs

# 配置 Git
git config user.name "里斯本"
git config user.email "lisbon@local"

# 检查变更
if git status --porcelain | grep -q "."; then
    echo "📝 检测到文档变更..."
    
    # 添加所有变更
    git add -A
    
    # 提交
    git commit -m "docs: 自动提交 $(date '+%Y-%m-%d %H:%M')"
    
    # 推送
    export GIT_SSH_COMMAND="ssh -i ~/.ssh/github_key -o IdentitiesOnly=yes"
    git push origin master
    
    echo "✅ 自动提交完成"
else
    echo "✓ 无变更"
fi
