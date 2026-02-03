# 修改 QuarkFlow 技术开发方案

## TL;DR

> **Quick Summary**: 更新技术方案文档，补充最终定案的技术栈和工程级最佳实践约束
>
> **Deliverables**:
> - 更新 `docs/quark_flow_技术开发方案.md`
> - 新增技术栈定案章节
> - 新增工程级最佳实践（必做/不要做）
> - 更新模块设计强调 async 架构
>
> **Estimated Effort**: Short
> **Parallel Execution**: NO - 单文件修改
> **Critical Path**: 更新文档

---

## Context

### Original Request
用户要求修改 `docs/quark_flow_技术开发方案.md`，补充以下内容：
- 推荐技术栈（最终定案）：Python 3.11, asyncio, Telethon, httpx, Playwright (fallback), SQLite, Docker
- 工程级最佳实践（必做/不要做）：全 async、先写状态再做动作、单实例

### Interview Summary
**Key Discussions**:
- 当前技术方案已存在，但缺少技术栈定案和工程约束
- 需要明确 async 架构和最佳实践
- 强调"先写状态再做动作"的核心原则

**Research Findings**:
- 现有文档第 4 节技术选型需要更新为最终定案
- 第 5 节核心模块设计需要强调 async 架构
- 第 7 节去重设计需要明确"先写状态"原则

### Metis Review
**Identified Gaps** (addressed):
- 缺少工程级最佳实践章节 → 新增第 4.7 节
- 技术栈不够明确 → 更新为"最终定案"标识
- async 架构强调不足 → 在各模块设计中补充

---

## Work Objectives

### Core Objective
更新 QuarkFlow 技术开发方案文档，补充最终定案的技术栈和工程级最佳实践。

### Concrete Deliverables
- 更新后的 `docs/quark_flow_技术开发方案.md`

### Definition of Done
- [ ] 文档更新完成
- [ ] 技术栈章节明确标注"最终定案"
- [ ] 新增工程级最佳实践章节（第 4.7 节）
- [ ] 所有模块设计强调 async 架构
- [ ] 去重设计明确"先写状态"原则

### Must Have
- Python 3.11 + asyncio 全异步架构
- httpx + Playwright fallback 分层策略
- "先写状态再做动作"的核心约束
- 单实例运行限制

### Must NOT Have (Guardrails)
- 不改变文档整体结构（只更新内容）
- 不删除现有章节
- 不改变项目目标和架构（只补充细节）

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
>
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.

### Test Decision
- **Infrastructure exists**: NO（文档修改不需要测试）
- **Automated tests**: None
- **Framework**: None

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

**文档验证场景：**

```
Scenario: 文档更新完成验证
  Tool: Bash (grep)
  Preconditions: 文件已更新
  Steps:
    1. grep "最终定案" docs/quark_flow_技术开发方案.md
    2. Assert: 输出包含 "技术选型（最终定案）"
    3. grep "工程级最佳实践" docs/quark_flow_技术开发方案.md
    4. Assert: 输出包含 "## 4.7 工程级最佳实践（核心约束）"
    5. grep "asyncio" docs/quark_flow_技术开发方案.md
    6. Assert: 输出至少包含 5 处 "async"
    7. grep "先写状态" docs/quark_flow_技术开发方案.md
    8. Assert: 输出包含 "所有状态先写 DB，再做动作"
  Expected Result: 所有关键更新都已应用到文档
  Evidence: grep 命令输出

Scenario: 文档语法验证
  Tool: Bash
  Preconditions: 文件已更新
  Steps:
    1. wc -l docs/quark_flow_技术开发方案.md
    2. Assert: 行数 > 400（新增内容后应该更长）
    3. grep -c "## " docs/quark_flow_技术开发方案.md
    4. Assert: 章节数量合理（至少 10 个主要章节）
  Expected Result: 文档结构完整
  Evidence: 命令输出
```

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately):
└── Task 1: 更新技术选型章节（第 4 节）

Wave 2 (After Wave 1):
├── Task 2: 新增工程级最佳实践（第 4.7 节）
└── Task 3: 更新 TelegramListener 设计（第 5.1 节）

Wave 3 (After Wave 2):
├── Task 4: 更新 QuarkClient 设计（第 5.4 节）
└── Task 5: 更新去重设计强调（第 7 节）

Critical Path: Task 1 → Task 2 → Task 3 → Task 4 → Task 5
Parallel Speedup: 部分 tasks 可并行（3, 4, 5）
```

---

## TODOs

- [ ] 1. 更新技术选型章节（第 4 节）

  **What to do**:
  - 更新第 4 节标题为 "技术选型（最终定案）"
  - 补充技术栈明细：Python 3.11, asyncio, Telethon, httpx, Playwright (fallback), SQLite, Docker
  - 更新 4.2 节强调 Telethon 的 async 特性
  - 新增 4.3 节 HTTP 客户端（httpx）
  - 更新 4.5 节夸克网盘自动化为分层策略（httpx + Playwright fallback）

  **Must NOT do**:
  - 不改变现有章节结构
  - 不删除 4.1, 4.2, 4.3, 4.4, 4.5, 4.6 的编号

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `writing`
    - Reason: 文档编写任务，需要精确的文本编辑
  - **Skills**: N/A
  - **Skills Evaluated but Omitted**:
    - 无需特定技能

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: Task 2, 3, 4, 5
  - **Blocked By**: None (can start immediately)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `docs/quark_flow_技术开发方案.md:55-100` - 第 4 节现有结构

  **API/Type References** (contracts to implement against):
  - N/A

  **Test References** (testing patterns to follow):
  - N/A

  **Documentation References** (specs and requirements):
  - 用户提供的最终技术栈清单

  **External References** (libraries and frameworks):
  - N/A

  **WHY Each Reference Matters** (explain the relevance):
  - 需要读取现有文档结构，保持格式一致性

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  ```
  Scenario: 第 4 节技术选型更新验证
    Tool: Bash (grep/sed)
    Preconditions: 文件已编辑
    Steps:
      1. grep "技术选型（最终定案）" docs/quark_flow_技术开发方案.md
      2. Assert: 匹配到标题 "## 4. 技术选型（最终定案）"
      3. grep "Language: Python 3.11" docs/quark_flow_技术开发方案.md
      4. Assert: 输出包含该行
      5. grep "Async: asyncio" docs/quark_flow_技术开发方案.md
      6. Assert: 输出包含该行
      7. grep "HTTP: httpx" docs/quark_flow_技术开发方案.md
      8. Assert: 输出包含该行
      9. grep "Browser: Playwright (fallback)" docs/quark_flow_技术开发方案.md
      10. Assert: 输出包含该行
    Expected Result: 技术栈信息完整更新
    Evidence: grep 输出

  Scenario: HTTP 客户端章节验证
    Tool: Bash
    Preconditions: 文件已编辑
    Steps:
      1. grep -A 10 "### 4.3 HTTP 客户端" docs/quark_flow_技术开发方案.md
      2. Assert: 输出包含 "httpx"
      3. Assert: 输出包含 "异步"
      4. Assert: 输出包含 "async"
    Expected Result: 新的 4.3 节内容正确
    Evidence: grep 输出
  ```

  **Evidence to Capture**:
  - [ ] grep 命令输出作为验证证据

  **Commit**: NO

---

- [ ] 2. 新增工程级最佳实践章节（第 4.7 节）

  **What to do**:
  - 在第 4 节末尾新增 "## 4.7 工程级最佳实践（核心约束）"
  - 包含 "✅ 必做" 和 "❌ 不要做" 两个子章节
  - 必做内容：所有外部 IO 都 async、所有状态先写 DB 再做动作、单实例运行
  - 不要做内容：先请求再去重、转存成功再写状态、cron + 脚本拼凑
  - 包含代码示例对比（错误 vs 正确）

  **Must NOT do**:
  - 不改变现有 4.1-4.6 章节内容
  - 不插入到第 5 节之后

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: 文档新增任务
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: Task 3, 4, 5
  - **Blocked By**: Task 1

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `docs/quark_flow_技术开发方案.md:95-100` - 第 4 节结尾位置

  **API/Type References** (contracts to implement against):
  - N/A

  **Test References** (testing patterns to follow):
  - N/A

  **Documentation References** (specs and requirements):
  - 用户提供的最佳实践清单

  **External References** (libraries and frameworks):
  - N/A

  **WHY Each Reference Matters** (explain the relevance):
  - 需要找到正确的插入位置（第 4 节末尾，第 5 节之前）

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  ```
  Scenario: 工程级最佳实践章节验证
    Tool: Bash
    Preconditions: 文件已更新
    Steps:
      1. grep "## 4.7 工程级最佳实践" docs/quark_flow_技术开发方案.md
      2. Assert: 匹配到该标题
      3. grep -A 5 "✅ 必做" docs/quark_flow_技术开发方案.md
      4. Assert: 输出包含 "所有外部 IO 都 async"
      5. Assert: 输出包含 "所有状态先写 DB，再做动作"
      6. Assert: 输出包含 "单实例运行"
      7. grep -A 5 "❌ 不要做" docs/quark_flow_技术开发方案.md
      8. Assert: 输出包含 "不要「先请求再去重」"
      9. Assert: 输出包含 "不要「转存成功再写状态」"
      10. Assert: 输出包含 "不要用 cron + 脚本拼凑"
    Expected Result: 最佳实践章节完整
    Evidence: grep 输出

  Scenario: 代码示例验证
    Tool: Bash
    Preconditions: 文件已更新
    Steps:
      1. grep -c "```python" docs/quark_flow_技术开发方案.md
      2. Assert: Python 代码块数量 >= 2（错误示例和正确示例）
      3. grep "❌ 错误" docs/quark_flow_技术开发方案.md
      4. Assert: 至少 3 处错误示例标注
      5. grep "✅ 正确" docs/quark_flow_技术开发方案.md
      6. Assert: 至少 3 处正确示例标注
    Expected Result: 代码示例完整且有对比
    Evidence: grep 输出
  ```

  **Evidence to Capture**:
  - [ ] grep 输出

  **Commit**: NO

---

- [ ] 3. 更新 TelegramListener 设计（第 5.1 节）

  **What to do**:
  - 更新第 5.1 节 TelegramListener 描述
  - 强调使用 `async def` 实现所有方法
  - 补充 Telethon 异步特性说明
  - 消息处理流程改为异步架构

  **Must NOT do**:
  - 不改变模块职责描述
  - 不删除关键点和去重逻辑

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: 文档更新
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 4, 5)
  - **Blocks**: None
  - **Blocked By**: Task 1, 2

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `docs/quark_flow_技术开发方案.md:105-115` - 第 5.1 节现有内容

  **API/Type References** (contracts to implement against):
  - N/A

  **Test References** (testing patterns to follow):
  - N/A

  **Documentation References** (specs and requirements):
  - Telethon 官方文档（异步使用）

  **External References** (libraries and frameworks):
  - N/A

  **WHY Each Reference Matters** (explain the relevance):
  - 需要保持原有结构，只补充 async 说明

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  ```
  Scenario: TelegramListener async 更新验证
    Tool: Bash
    Preconditions: 文件已更新
    Steps:
      1. grep -A 15 "### 5.1 TelegramListener" docs/quark_flow_技术开发方案.md
      2. Assert: 输出包含 "async"
      3. Assert: 输出包含 "Telethon"
      4. Assert: 输出包含 "异步"
      5. grep "asyncio" docs/quark_flow_技术开发方案.md | grep -A 5 -B 5 "5.1"
      6. Assert: 在第 5.1 节附近提到 asyncio
    Expected Result: TelegramListener 设计强调异步
    Evidence: grep 输出
  ```

  **Evidence to Capture**:
  - [ ] grep 输出

  **Commit**: NO

---

- [ ] 4. 更新 QuarkClient 设计（第 5.4 节）

  **What to do**:
  - 更新第 5.4 节 QuarkClient 描述
  - 明确分层策略：首选 httpx，兜底 Playwright
  - 强调所有方法都是 `async def`
  - 补充 httpx.AsyncClient 使用说明
  - 补充 Playwright fallback 触发条件

  **Must NOT do**:
  - 不改变模块职责
  - 不删除安全策略

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: 文档更新
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 3, 5)
  - **Blocks**: None
  - **Blocked By**: Task 1, 2

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `docs/quark_flow_技术开发方案.md:142-152` - 第 5.4 节现有内容

  **API/Type References** (contracts to implement against):
  - N/A

  **Test References** (testing patterns to follow):
  - N/A

  **Documentation References** (specs and requirements):
  - 用户提供的分层策略说明

  **External References** (libraries and frameworks):
  - N/A

  **WHY Each Reference Matters** (explain the relevance):
  - 需要在现有职责基础上补充技术细节

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  ```
  Scenario: QuarkClient 分层策略验证
    Tool: Bash
    Preconditions: 文件已更新
    Steps:
      1. grep -A 20 "### 5.4 QuarkClient" docs/quark_flow_技术开发方案.md
      2. Assert: 输出包含 "httpx"
      3. Assert: 输出包含 "Playwright"
      4. Assert: 输出包含 "fallback"
      5. Assert: 输出包含 "async"
      6. Assert: 输出包含 "AsyncClient"
    Expected Result: QuarkClient 设计明确分层策略和异步
    Evidence: grep 输出
  ```

  **Evidence to Capture**:
  - [ ] grep 输出

  **Commit**: NO

---

- [ ] 5. 更新去重设计强调（第 7 节）

  **What to do**:
  - 更新第 7 节去重与幂等设计
  - 在 7.5 工程实现约束中强调 "先写状态再做动作"
  - 更新 7.4 去重决策流程图，突出 pending 状态先于操作
  - 补充说明：状态变更是真理，外部操作是副作用

  **Must NOT do**:
  - 不改变三层去重策略结构
  - 不删除数据表设计

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: 文档更新
  - **Skills**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 3, 4)
  - **Blocks**: None
  - **Blocked By**: Task 1, 2

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `docs/quark_flow_技术开发方案.md:313-322` - 第 7.5 节现有内容

  **API/Type References** (contracts to implement against):
  - N/A

  **Test References** (testing patterns to follow):
  - N/A

  **Documentation References** (specs and requirements):
  - 用户提供的最佳实践清单

  **External References** (libraries and frameworks):
  - N/A

  **WHY Each Reference Matters** (explain the relevance):
  - 需要强化"先写状态"的核心约束

  **Acceptance Criteria**:

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  ```
  Scenario: 去重设计约束验证
    Tool: Bash
    Preconditions: 文件已更新
    Steps:
      1. grep -A 10 "### 7.5 工程实现约束" docs/quark_flow_技术开发方案.md
      2. Assert: 输出包含 "先写状态"
      3. Assert: 输出包含 "pending"
      4. Assert: 输出包含 "状态变更是真理"
      5. grep -A 30 "去重决策完整流程" docs/quark_flow_技术开发方案.md
      6. Assert: 流程图中 "创建 pending 任务" 在 "执行夸克转存" 之前
    Expected Result: 去重设计强调先写状态原则
    Evidence: grep 输出
  ```

  **Evidence to Capture**:
  - [ ] grep 输出

  **Commit**: NO

---

## Success Criteria

### Verification Commands
```bash
# 验证技术栈更新
grep "最终定案" docs/quark_flow_技术开发方案.md
grep "Language: Python 3.11" docs/quark_flow_技术开发方案.md
grep "httpx" docs/quark_flow_技术开发方案.md

# 验证最佳实践章节
grep "## 4.7 工程级最佳实践" docs/quark_flow_技术开发方案.md
grep "所有外部 IO 都 async" docs/quark_flow_技术开发方案.md
grep "所有状态先写 DB，再做动作" docs/quark_flow_技术开发方案.md

# 验证 async 强调
grep -c "async" docs/quark_flow_技术开发方案.md | awk '{if($1>5) print "OK"; else print "FAIL"}'
```

### Final Checklist
- [ ] 第 4 节技术选型标注"最终定案"
- [ ] 第 4.7 节工程级最佳实践已新增
- [ ] TelegramListener 设计强调 async
- [ ] QuarkClient 设计明确 httpx + Playwright fallback
- [ ] 去重设计强调"先写状态再做动作"
- [ ] 所有包含代码示例的地方有错误 vs 正确对比
