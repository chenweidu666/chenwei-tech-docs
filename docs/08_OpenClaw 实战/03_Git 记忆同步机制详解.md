<div style="text-align: center; font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;"><strong>Git 记忆同步机制详解</strong></div>
> 2026-03-25 | 🦞 双龙虾架构实战系列第 3 篇

---

- [同步架构](#同步架构)
- [文件权限设计](#文件权限设计)
- [同步脚本详解](#同步脚本详解)
- [冲突解决](#冲突解决)
- [安全配置](#安全配置)
- [性能优化](#性能优化)
- [故障排查](#故障排查)


---

## 📋 目录

- [同步架构](#同步架构)
- [文件权限设计](#文件权限设计)
- [同步脚本详解](#同步脚本详解)
- [冲突解决](#冲突解决)
- [安全配置](#安全配置)
- [性能优化](#性能优化)
- [故障排查](#故障排查)

---

## 同步架构

### 为什么选择 Git？

| 方案 | 实时性 | 可靠性 | 复杂度 | 选择 |
|------|--------|--------|--------|------|
| **Git 仓库** | ⭐⭐⭐ 异步 | ⭐⭐⭐⭐⭐ 高 | ⭐⭐ 低 | ✅ |
| WebSocket | ⭐⭐⭐⭐⭐ 实时 | ⭐⭐⭐ 中 | ⭐⭐⭐⭐ 高 | ❌ |
| 数据库同步 | ⭐⭐⭐⭐ 准实时 | ⭐⭐⭐⭐ 高 | ⭐⭐⭐⭐ 高 | ❌ |
| 文件共享 | ⭐⭐⭐ 异步 | ⭐⭐ 低 | ⭐⭐ 低 | ❌ |

**Git 优势**：
- ✅ 有历史记录，可追溯
- ✅ 冲突检测机制完善
- ✅ 无需额外服务
- ✅ 天然支持离线操作

---

### 同步拓扑

```
┌──────────────────────────────────────┐
│         GitHub GateClaw-Bot           │
│          (同步中枢/中转站)             │
└──────────────┬───────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   ┌─────────┐   ┌─────────┐
   │ 里斯本   │   │ 尤力克   │
   │ 推/拉    │   │ 只拉为主 │
   └─────────┘   └─────────┘
```

---

## 文件权限设计

### 文件分类

| 文件类型 | 写入方 | 读取方 | 同步方向 |
|---------|--------|--------|---------|
| **记忆文件** | | | |
| MEMORY.md | 里斯本 | 双方 | 里斯本 → 尤力克 |
| memory/*.md | 里斯本 | 双方 | 里斯本 → 尤力克 |
| **交易文件** | | | |
| position_tracking.md | 尤力克 | 双方 | 尤力克 → 里斯本 |
| trade_log/*.md | 尤力克 | 里斯本 (只读) | 尤力克 → 里斯本 |
| **配置文件** | | | |
| IDENTITY.md | 各自维护 | 仅自己 | 不同步 |
| SOUL.md | 各自维护 | 仅自己 | 不同步 |
| USER.md | 里斯本 | 双方 | 里斯本 → 尤力克 |
| **消息文件** | | | |
| MESSAGE_*.md | 双方 | 双方 | 双向 |

### 权限控制

**里斯本权限**：
```bash
# 可写
MEMORY.md ✅
memory/*.md ✅
USER.md ✅

# 只读
position_tracking.md 📖
trade_log/*.md 📖
```

**尤力克权限**：
```bash
# 可写
position_tracking.md ✅
trade_log/*.md ✅

# 只读
MEMORY.md 📖
memory/*.md 📖
USER.md 📖
```

---

## 同步脚本详解

### 里斯本同步脚本

**位置**：`/root/.openclaw/workspace/GateClaw-Bot/scripts/sync-memory.sh`

```bash
#!/bin/bash
# GateClaw-Bot 记忆同步脚本
# 里斯本 (Lisbon) 版本 - 路径：/root/.openclaw/workspace/

set -e
cd /root/.openclaw/workspace/GateClaw-Bot

# 配置 SSH key
export GIT_SSH_COMMAND="ssh -i ~/.ssh/github_key -o IdentitiesOnly=yes"
git config core.sshCommand "ssh -i ~/.ssh/github_key -o IdentitiesOnly=yes"

echo "📥 拉取最新提交..."
git pull origin master 2>/dev/null || true

# 里斯本负责：MEMORY.md、memory/*.md、USER.md 等上下文记忆
# 从仓库同步到本地工作区
echo "📋 同步 MEMORY.md..."
cp -f MEMORY.md /root/.openclaw/workspace/MEMORY.md 2>/dev/null || true

echo "📋 同步 memory/*.md..."
cp -f memory/*.md /root/.openclaw/workspace/memory/ 2>/dev/null || true

# 合并尤力克的交易数据到 MEMORY.md（只读 position_tracking.md）
if [ -f position_tracking.md ]; then
    echo "📊 读取交易数据..."
    # 这里可以添加逻辑：从 position_tracking.md 提取关键信息合并到 MEMORY.md
fi

# 提交并推送变更（只推送里斯本负责的文件）
if git status --porcelain | grep -q "."; then
    echo "💾 提交变更..."
    git add MEMORY.md memory/*.md USER.md SOUL.md IDENTITY.md TOOLS.md 2>/dev/null || true
    git commit -m "sync: 记忆同步 $(date '+%Y-%m-%d %H:%M UTC')" || {
        echo "✓ 无变更需要提交"
        exit 0
    }
    git push origin master
    echo "✅ 同步完成"
else
    echo "✓ 已是最新"
fi
```

**Cron 配置**：
```json
{
  "name": "gateclaw-memory-sync",
  "schedule": "0 */2 * * *",
  "command": "/root/.openclaw/workspace/GateClaw-Bot/scripts/sync-memory.sh",
  "enabled": true,
  "timezone": "Asia/Shanghai"
}
```

**执行频率**：每 2 小时

---

### 尤力克同步脚本

**位置**：`/home/node/.openclaw/workspace/GateClaw-Bot/scripts/sync-from-lisbon.sh`

```bash
#!/bin/bash
# 尤力克同步脚本 - 只拉取不推送

set -e
cd /home/node/.openclaw/workspace/GateClaw-Bot

# 配置 SSH
export GIT_SSH_COMMAND="ssh -i ~/.ssh/github_key -o IdentitiesOnly=yes"

echo "📥 拉取里斯本的更新..."
git pull origin master

# 同步记忆文件到本地
cp -f MEMORY.md /home/node/.openclaw/workspace/MEMORY.md
cp -f memory/*.md /home/node/.openclaw/workspace/memory/

echo "✅ 同步完成"
```

**Cron 配置**：
```json
{
  "name": "sync-from-lisbon",
  "schedule": "*/30 * * * *",
  "command": "/home/node/.openclaw/workspace/GateClaw-Bot/scripts/sync-from-lisbon.sh",
  "enabled": true
}
```

**执行频率**：每 30 分钟

---

## 冲突解决

### 冲突场景

**场景 1：同时修改 MEMORY.md**

```
里斯本：git pull → 修改 MEMORY.md → git commit
尤力克：git pull → 修改 MEMORY.md → git commit (冲突！)
```

**解决方案**：
1. **权限隔离** - 尤力克不写 MEMORY.md
2. **rebase 优先** - `git pull --rebase`
3. **文件锁** - 写入前检查 `.lock` 文件

---

### 文件锁机制

**锁文件**：`.sync.lock`

**里斯本加锁**：
```bash
# 写入前检查锁
if [ -f .sync.lock ]; then
    echo "⚠️ 同步锁已存在，等待释放..."
    sleep 60
fi

# 加锁
echo "lisbon:$(date)" > .sync.lock

# 执行同步操作
# ...

# 释放锁
rm -f .sync.lock
```

**尤力克检查锁**：
```bash
# 检查锁
if [ -f .sync.lock ]; then
    lock_owner=$(cat .sync.lock | cut -d: -f1)
    lock_time=$(cat .sync.lock | cut -d: -f2)
    
    # 如果锁超过 1 小时，强制释放
    if [ $(( $(date +%s) - $(date -d "$lock_time" +%s) )) -gt 3600 ]; then
        echo "⚠️ 检测到 stale lock，强制释放"
        rm -f .sync.lock
    fi
fi
```

---

### Rebase 策略

**推荐配置**：
```bash
# 全局配置
git config --global pull.rebase true

# 仓库配置
cd /root/.openclaw/workspace/GateClaw-Bot
git config pull.rebase true
```

**Rebase 流程**：
```bash
# 1. 保存本地修改
git stash

# 2. 拉取远程
git pull --rebase origin master

# 3. 恢复本地修改
git stash pop

# 4. 提交
git add .
git commit -m "sync: merged changes"
git push
```

---

## 安全配置

### SSH Key 配置

**生成 SSH Key**：
```bash
ssh-keygen -t ed25519 -C "lisbon@openclaw" -f ~/.ssh/github_key
```

**配置权限**：
```bash
chmod 600 ~/.ssh/github_key
chmod 644 ~/.ssh/github_key.pub
```

**添加到 GitHub**：
1. 复制公钥：`cat ~/.ssh/github_key.pub`
2. 打开 https://github.com/settings/keys
3. 点击 "New SSH key"
4. 粘贴公钥，保存

**Git 配置**：
```bash
# 全局配置 SSH
git config --global core.sshCommand "ssh -i ~/.ssh/github_key -o IdentitiesOnly=yes"

# URL 替换（HTTPS → SSH）
git config --global url."ssh://git@github.com/".insteadOf "https://github.com/"
```

---

### Token 安全

**GitHub Token**：
```bash
# 存储在安全位置
mkdir -p ~/.openclaw/secrets
echo "ghp_xxx" > ~/.openclaw/secrets/github_token
chmod 600 ~/.openclaw/secrets/github_token
```

**环境变量**：
```bash
# 在脚本中使用
export GITHUB_TOKEN=$(cat ~/.openclaw/secrets/github_token)

# 或在.git/config 中配置
[credential]
    helper = store
```

---

## 性能优化

### 批量提交

**问题**：频繁小提交导致 Git 历史冗长

**优化**：
```bash
# 积累多个变更再提交
if [ $(git status --porcelain | wc -l) -ge 5 ]; then
    git add -A
    git commit -m "sync: batch update ($(date '+%Y-%m-%d %H:%M'))"
    git push
fi
```

---

### 浅克隆

**首次克隆**：
```bash
git clone --depth 1 git@github.com:chenweidu666/GateClaw-Bot.git
```

**定期清理**：
```bash
# 清理 reflog
git reflog expire --expire=now --all

# 垃圾回收
git gc --prune=now --aggressive
```

---

### 增量同步

**只同步变更文件**：
```bash
# 检测变更
changed_files=$(git diff --name-only HEAD origin/master)

# 只同步变更的记忆文件
for file in $changed_files; do
    if [[ $file == memory/*.md ]] || [[ $file == "MEMORY.md" ]]; then
        cp -f $file /root/.openclaw/workspace/$file
        echo "📋 同步：$file"
    fi
done
```

---

## 故障排查

### 常见问题

**问题 1：SSH 认证失败**
```
fatal: Could not read from remote repository.
Permission denied (publickey).
```

**解决**：
```bash
# 检查 SSH key 权限
ls -la ~/.ssh/github_key

# 测试 SSH 连接
ssh -i ~/.ssh/github_key -T git@github.com

# 配置 Git 使用 SSH
git config core.sshCommand "ssh -i ~/.ssh/github_key -o IdentitiesOnly=yes"
```

---

**问题 2：冲突无法解决**
```
CONFLICT (content): Merge conflict in MEMORY.md
```

**解决**：
```bash
# 1. 查看冲突
git diff MEMORY.md

# 2. 手动编辑解决冲突
vim MEMORY.md

# 3. 标记解决
git add MEMORY.md

# 4. 继续 rebase
git rebase --continue

# 5. 推送
git push
```

---

**问题 3：推送被拒绝**
```
! [rejected] master -> master (fetch first)
```

**解决**：
```bash
# 先拉取
git pull --rebase origin master

# 再推送
git push origin master

# 或强制推送（慎用）
git push -f origin master
```

---

**问题 4：同步脚本不执行**
```bash
# 检查 Cron 状态
systemctl status cron

# 查看 Cron 日志
grep CRON /var/log/syslog | tail -20

# 手动测试脚本
bash /root/.openclaw/workspace/GateClaw-Bot/scripts/sync-memory.sh
```

---

## 监控与告警

### 同步状态监控

**Dashboard 集成**：
```javascript
// 在 Dashboard 中添加同步状态组件
const syncStatus = {
  lisbon: {
    lastSync: '2026-03-25 14:00',
    status: '✅',
    nextSync: '2026-03-25 16:00'
  },
  eureka: {
    lastSync: '2026-03-25 14:30',
    status: '✅',
    nextSync: '2026-03-25 15:00'
  }
};
```

---

### 告警规则

| 告警 | 触发条件 | 通知方式 |
|------|---------|---------|
| 同步失败 | 连续 3 次失败 | Telegram |
| 冲突未解决 | 超过 1 小时 | Telegram + 邮件 |
| Git 仓库不可达 | 连续 5 次失败 | Telegram |
| 磁盘空间不足 | < 10% | Telegram |

---

## 下一篇

👉 [04_OpenClaw 本地部署指南](./04_OpenClaw 本地部署指南.md)

---

*本文档由 里斯本 🦞 自动记录 | Powered by OpenClaw + Claude*
