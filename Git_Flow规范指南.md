# Git Flow 规范指南

> 适用项目：`ai-and-us` MUD 洞穴探险游戏  
> 适用阶段：Sprint 3 及后续迭代  
> 依据：作业要求"各组员必须创建独立的 feature/* 分支进行开发，并在发起 PR 前完成反向同步主干的冲突预解决，记录至少两次完整的 PR 评审过程"

---

## 一、分支结构

```
main                    ← 主干，始终保持 Green Build，只接受 PR 合并
├── feature/PB-01-combat-service      
├── feature/PB-02-save-restore-fix     
├── feature/PB-03-json-repository     
├── feature/PB-04-checkpoint-service   
└── feature/PB-05-test-coverage       
```

| 分支类型 | 命名规范 | 说明 |
|----------|----------|------|
| 主干 | `main` | 保护分支，禁止直接 push |
| 功能分支 | `feature/<PB编号>-<简短描述>` | 每个 Backlog 任务对应一个分支 |
| 修复分支 | `fix/<问题简述>` | 紧急 bug 修复 |

---

## 二、每位组员的完整开发流程

### 第 1 步：从 main 创建功能分支

```bash
# 确保本地 main 是最新的
git checkout main
git pull origin main

# 创建并切换到功能分支（以 PB-01 为例）
git checkout -b feature/PB-01-combat-service
```

### 第 2 步：开发并提交

```bash
# 开发完成后，小步提交，提交信息遵循规范
git add game/services/combat_service.py tests/test_combat_service.py
git commit -m "feat(combat): extract CombatService from GameEngine"

# 推送到远端
git push origin feature/PB-01-combat-service
```

**提交信息规范：**

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(combat): extract CombatService` |
| `fix` | bug 修复 | `fix(save): restore enemy hp on load` |
| `refactor` | 重构 | `refactor(engine): delegate attack to CombatService` |
| `test` | 测试 | `test(combat): add 5 branch tests for attack()` |
| `docs` | 文档 | `docs: update Product_Backlog` |

### 第 3 步：发起 PR 前的反向同步（必须执行）

> 目的：在 PR 前把 main 的最新变更合并进自己的分支，在本地解决冲突，而不是把冲突留给评审人。

```bash
# 切回 main，拉取最新
git checkout main
git pull origin main

# 切回功能分支，合并 main
git checkout feature/PB-01-combat-service
git merge main

# 如果有冲突，在本地解决后提交
# git add <冲突文件>
# git commit -m "merge: sync with main before PR"

# 推送更新后的分支
git push origin feature/PB-01-combat-service
```

### 第 4 步：在 GitHub 发起 Pull Request

1. 打开仓库页面，点击 "Compare & pull request"
2. 填写 PR 描述（见下方模板）
3. 指定至少 1 名 Reviewer（其他组员）
4. 确认 CI 全部绿色后，等待评审

**PR 描述模板：**

```
## 本次变更

- 提取 CombatService，将 attack_enemy() 拆分为 4 个职责单一的方法
- GameEngine.attack_enemy() 重构为薄包装

## 关联任务

- 关闭 PB-01

## 验收标准确认

- [x] CombatService 独立可实例化，不依赖 GameEngine
- [x] GameEngine.attack_enemy() 圈复杂度降至 ≤ 5
- [x] 原有 21 个测试用例全部通过
- [x] 新增战斗分支测试 5 个

## 测试截图 / CI 状态

（粘贴 CI Green Build 截图）
```

### 第 5 步：PR 评审规范

**评审人职责：**
- 检查代码是否符合 DDS 设计方案
- 确认测试覆盖了 DDS §6.3 要求的分支
- 确认 CI 全部通过
- 留下至少 1 条具体评审意见（不能只点 Approve）

**评审意见示例：**
```
# 建议修改
CombatService.__init__ 直接接收 CheckpointService 实例，
建议改为依赖注入，方便测试时传入 Mock 对象。

# 确认通过
attack() 的五类分支测试覆盖完整，逻辑清晰，LGTM。
```

### 第 6 步：合并与清理

```bash
# PR 通过后，在 GitHub 页面点击 "Squash and merge"
# 合并后删除远端功能分支（GitHub 页面有提示）

# 本地同步并清理
git checkout main
git pull origin main
git branch -d feature/PB-01-combat-service
```

---

## 三、Sprint 3 各成员分支计划

| 成员 | 分支 | 对应任务 | 依赖 |
|------|------|----------|------|
| 张津毓 | `feature/PB-02-save-restore-fix` | 修复存档读档房间状态恢复 | 无 |
| 张津毓 | `feature/PB-03-json-repository` | 提取 JsonSaveRepository | PB-02 |
| 曹睿杰 | `feature/PB-01-combat-service` | 提取 CombatService | 无 |
| 曹睿杰 | `feature/PB-04-checkpoint-service` | 提取 CheckpointService | PB-01 |
| 张津毓 | `feature/PB-05-test-coverage` | 补全服务层测试 | PB-01~04 |
| 王鹏 | `feature/PB-07-legacy-adapter` | 引入 LegacyCommandAdapter | PB-01~04 |
| 王鹏 | `feature/PB-08-world-builder` | 引入 WorldBuilder 工厂 | PB-03 |

---

## 四、PR 评审记录模板

每次 PR 合并后，在下方追加记录（作业要求至少 2 次）：

### PR #___ — ___（功能名称）

| 项目 | 内容 |
|------|------|
| 分支 | `feature/PB-XX-xxx` → `main` |
| 提交人 | |
| 评审人 | |
| PR 发起时间 | |
| 合并时间 | |
| CI 状态 | ✅ Green / ❌ Failed |
| 主要评审意见 | |
| 是否要求修改后重新提交 | 是 / 否 |

---

## 五、常见问题

**Q：反向同步时遇到冲突怎么办？**  
用 VS Code 的合并编辑器打开冲突文件，保留正确的代码后 `git add` 再 `git commit`，不要直接 `git push --force`。

**Q：CI 红了能合并吗？**  
不能。必须在功能分支上修复到 CI 全绿后才能请求合并。

**Q：可以直接 push 到 main 吗？**  
不可以。main 是保护分支，所有变更必须通过 PR + 至少 1 人 Approve 才能合并。

---

**最后更新：** 2026 年 4 月 15 日
