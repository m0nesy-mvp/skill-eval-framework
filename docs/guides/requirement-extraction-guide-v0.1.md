# 《Requirement Extraction Guide v0.1》

Status: Design Guide
Version: v0.1
Date: 2026-08-24

## 1. 目的

本 Guide 定义 Part 1 Agent 如何理解 Target Skill，并从规范性来源中提取完整、可审查、可追溯的 Final Requirement Set。

它细化《通用 Skill Eval Design Process v1.1（Scope-Frozen）》中的 Step 1 `Skill Understanding & Scope` 和 Step 2 `Requirement Extraction`，不替代已经冻结的 Concept Model，也不修改已经冻结的 Benchmark Definition / Requirement / Contract Schema。

Requirement Extraction 必须分别回答：

1. 这个 Skill 在规范意义上要求什么？
2. 哪些责任应进入 Final Requirement Set，应采用什么粒度，又如何回溯来源？

不能仅仅因为当前实现表现出某种行为，就推导出一条 Requirement。

## 2. 范围与非目标

本 Guide 覆盖：

- 以足够范围阅读 Skill，形成可靠理解；
- 区分 Normative Source 与 Implementation Fact；
- 收集、规范化和追溯 Requirement Candidate；
- 将 Requirement 分类为 `outcome` 或 `workflow`；
- 处理重复、粒度、不确定性和来源冲突；
- 形成四项必需的 Requirement Extraction 产物。

本 Guide 不负责：

- 定义 Contract 的 success criteria 或 failure criteria；
- 编写 Grader assertion 或评分逻辑；
- 设计 Test Case、Evidence、Metric、Rubric 或 Gate；
- 新增 `constraint`、`mixed` 或任何第三种 `evaluation_type`；
- 规定固定的 Requirement 数量区间；
- 修改已经冻结的 Requirement Schema；
- 要求机械读取 Skill 目录中的所有文件；
- 默认将当前实现行为视为规范性来源。

一条 Requirement 能进入下一阶段的最低语义条件是：它能够继续被 Contract 化，并且违反它时存在具有独立意义的可观察失败。具体可执行检查不属于 Requirement Extraction。

## 3. 输入与最终产物

### 3.1 输入

Requirement Extraction 可以使用：

- Target Skill 及其入口 `SKILL.md`；
- 从 Skill 中识别出的规范性资源；
- 用户明确要求；
- 项目正式要求；
- 接口正式要求；
- 仅用于理解真实行为或发现冲突的相关 Implementation Fact；
- 当前 Eval 范围与已知非目标。

### 3.2 最终产物

Requirement Extraction 必须产生：

1. **Skill Summary**：Pass 1 的已审查理解结果；
2. **Requirement Candidate Ledger**：从收集到规范化过程中的可审查工作记录；
3. **Traceability Review**：集合级双向来源覆盖审查；
4. **Final Requirement Set**：只包含已接受 Requirement，并使用冻结的 Requirement Schema。

中间工作记录属于设计 Artifact。它们不会为冻结的 Requirement Schema 增加字段，也不会自动进入 Frozen Benchmark Definition。

## 4. Reading Scope：理解规范意义上的完整 Skill

### 4.1 `SKILL.md` 是入口，但不一定是完整规范

Requirement Extraction 面向规范意义上的完整 Skill。正常阅读流程是：

```text
SKILL.md
→ 识别规范性依赖
→ 按需读取 references / schemas / scripts / templates / config
→ 构建完整 Skill Understanding
```

Agent 从 `SKILL.md` 开始，识别能力结构和被引用依赖；只有在理解规范性责任、必需执行路径、输出标准或已知不确定项所需时，才扩展阅读范围。

不得机械读取所有文件。普通 assets、生成文件、无关示例、测试、缓存和内部 helper 不会自动进入规范性阅读范围。

### 4.2 规范性依赖判断

符合以下任一条件时，应读取被引用资源：

- 规范性来源声明该资源定义必需行为或输出；
- Skill 要求 Agent 遵循该资源；
- Skill 要求结果符合该资源；
- 理解某个能力分支或必需工作流离不开该资源；
- 该资源可能包含相互冲突的规范性指令；
- 不读取它就无法可靠完成 Pass 1。

读取一个资源，不代表其中所有内容都自动具有规范性。Agent 必须判断规范委托了什么责任，以及哪些内容与该委托有关。

### 4.3 复杂 Skill 的覆盖方式

对于复杂 Skill，Agent 应先识别：

- 跨整个 Skill 生效的 Shared 行为；
- 每一个能力分支；
- 分支特有的依赖与约束；
- Shared 输出与分支输出；
- 明确不在范围内的能力。

Pass 1 和 Pass 2 都必须覆盖 Shared 层以及每个 in-scope 能力分支。成功理解一个路径，不能证明已经理解整个 Skill。

## 5. Normative Source 与 Implementation Fact

### 5.1 Normative Source

Normative Source 能够产生 Requirement，例如：

- `SKILL.md`；
- 被 Skill 明确指定为正式标准的 reference；
- 最终结果必须符合的 schema；
- Skill 必须运行或通过的 validator；
- 必须遵循的 checklist；
- 必须使用的 template；
- 用户明确要求；
- 项目或接口正式要求。

最终 `source` 仍使用已经冻结的枚举：

```text
skill | user | project | interface | other
```

具体文件、章节、指令或资源在存在稳定位置时记录到 `source_ref`。

### 5.2 Implementation Fact

Implementation Fact 描述当前实现实际上怎样工作，例如：

- 当前 Python 行为；
- 当前 CLI 路由或输出；
- helper script 内部逻辑；
- 没有被规范声明的默认值；
- 当前实现限制。

Implementation Fact 可以用于理解真实行为、发现规范与实现冲突、定位问题或识别可能缺失的规范，但不能仅因为代码当前这样实现，就升级成 Requirement。

### 5.3 对资源的规范委托

script、schema、validator、template、reference 或 config，只有在 Normative Source 明确委托的范围内才成为正式标准的一部分。例如：

- “必须运行 validator X”委托了执行该 validator 的要求；
- “最终结果必须符合 schema Y”委托了 schema Y 中适用的输出规则；
- “必须使用 template Z”委托了该 template 所规定的结构或内容；
- “reference A 定义正式输出规范”委托了该 reference 中的输出规范。

Agent 必须把被委托资源读取到足以理解被委托责任的程度。同一资源中的无关实现细节不会自动变成 Requirement。

### 5.4 规范与实现不一致

当 Normative Source 与 Implementation Fact 不一致时：

- 保留规范陈述作为 Requirement 来源；
- 将实现差异记录为冲突或 review note；
- 不得静默把 Requirement 改写为当前实现行为；
- 没有后续阶段的运行证据时，不得声称实现满足 Requirement。

## 6. 四遍 Requirement Extraction 流程

四遍流程各有不同目标。不得把它们压缩成从原文直接生成正式 Requirement ID 的一次转换。

### 6.1 Pass 1 — Understand

**目标：**在提取正式 Requirement 前，理解完整的 in-scope Skill。

执行步骤：

1. 把 `SKILL.md` 作为入口读取。
2. 识别 Shared 行为和所有 in-scope 能力分支。
3. 识别 Normative Source 与规范性依赖。
4. 按需读取被委托或理解所必需的资源。
5. 区分规范声明的责任与 Implementation Fact。
6. 记录约束、排除项、未解析术语和来源冲突。
7. 判断当前理解是否足以开始系统收集 Candidate。

Skill Summary 必须包含：

- **Skill Summary**：目的、输入、输出和已声明能力；
- **Normal Execution Flow**：正常端到端路径及有意义的分支；
- **Important Dependencies**：理解 Skill 所需的资源、工具、schema、validator、template、config、服务或环境依赖；
- **Known Constraints**：顺序、授权、禁止行为、输出约束及其他正式限制；
- **Uncertainties**：缺失来源、歧义、未解决冲突和不可访问资源；
- **Decision**：`UNDERSTANDING_READY` 或 `UNDERSTANDING_BLOCKED`。

只有当 Agent 能解释完整的 in-scope Skill，并足以进行系统 Candidate 扫描时，才能输出 `UNDERSTANDING_READY`。

如果无法可靠理解 Skill，应输出 `UNDERSTANDING_BLOCKED`。例如：被委托的规范性资源缺失、关键能力分支无法访问，或未解决歧义会改变待提取责任。必须记录每个阻塞原因及其影响；不得静默停止，也不得假设缺失区域没有 Requirement。

### 6.2 Pass 2 — Collect

**目标：**以 recall 优先的方式收集 Requirement Candidate，但不提前宣布正式 Requirement。

规则：

- 使用 `RC-001`、`RC-002`、`RC-003` 等临时 ID；
- Collect 阶段不得分配 `R001` 等正式 ID；
- 分别扫描 Shared 行为和每一个 in-scope 能力分支；
- 不确定 Candidate 先保留，不要过早删除；
- 保存足够的来源上下文供后续审查；
- 记录来源是 normative，还是仅为 Implementation Fact；
- 不得在 Collect 阶段把示例、背景或普通实现细节变成已接受 Requirement。

本遍输出是已填充的 Requirement Candidate Ledger，不是 Final Requirement Set。

### 6.3 Pass 3 — Normalize

**目标：**把 Candidate 集合整理为一致的拟议 Requirement Set。

对每个 Candidate：

1. 执行 Split Test、Merge Test 和 Delete / Demote Test；
2. 去重并协调重叠表述；
3. 排除背景、示例和普通实现细节；
4. 决定不确定 Candidate 的处置；
5. 将接受的责任分类为 `outcome` 或 `workflow`；
6. 当 Outcome 与 Workflow 是独立责任时拆分混合陈述；
7. 将未解决的规范来源冲突标记为 `CONFLICT`；
8. 确认该陈述后续能够被 Contract 化，且违反时存在独立、有意义的可观察失败；
9. 在每次拆分或合并后保留来源追溯。

Normalize 可以产生 `keep`、`merge`、`remove`、`note`、`conflict / needs clarification` 等处置。只有已经解决的 `keep` 结果可以进入 Final Requirement Set。

### 6.4 Pass 4 — Trace

**目标：**在分配正式 Requirement ID 前完成集合级双向追溯审查。

必须审查两个方向：

```text
Normative Source → Requirement
Requirement → Normative Source
```

对于已经识别出的每一项 in-scope 规范内容，Traceability Review 必须给出：

- 至少一条映射到它的最终 Requirement；或
- 不进入 Final Requirement Set 的明确处置原因，例如 duplicate、background、example、out of scope、merged、note、conflict 或 needs clarification。

对于每一条最终 Requirement，必须确认合法来源、`source` 分类、可用的 `source_ref`，并确认它不是仅由 Implementation Fact 推导而来，且拆分和合并没有破坏来源追溯。

只有完成 Normalize 和 Traceability Review 后，才分配 `R001` 形式的正式 ID，并形成 Final Requirement Set。

## 7. Requirement Candidate Ledger

Candidate Ledger 是必需、可审查的中间产物。它是 Extraction 工作记录，不是冻结的 Requirement Schema。

至少在概念上记录：

| 字段 | 用途 |
|---|---|
| `candidate_id` | Extraction 阶段使用的临时 `RC-` ID |
| `candidate_statement` | 当前可能责任的陈述 |
| `capability / section` | Shared 区域、能力分支或相关章节 |
| `tentative evaluation type` | 暂定的 `outcome` 或 `workflow`；Collect 阶段可以未决定 |
| `source_ref` | 可能的规范性来源位置 |
| `source excerpt` | 人工审查所需的最小原文上下文 |
| `status` | candidate、keep、merge、remove、note、conflict 或 needs clarification 等当前处置 |
| `notes` | 理由、合并目标、实现差异、不确定项或审查上下文 |

Candidate Ledger 可以保留多个来源，尤其是 Candidate 合并或冲突记录。这样做不会修改最终 Requirement Schema。

拆分 Candidate 时，每个结果都必须保留适用的来源追溯。合并 Candidate 时，合并记录必须保留足以支持合并陈述的全部来源。

## 8. 粒度规则

Requirement 粒度由可观察责任和诊断价值决定，不由句子长度、bullet 数量或期望的 Requirement 数量决定。

### 8.1 Split Test

同时满足以下条件时，应拆分 A 与 B：

1. A 与 B 可以独立成功或失败；
2. 分别失败会产生两个可区分且值得单独记录的评估结论。

例如：

```text
执行规定的 validator
vs
产生通过该 validator 的结果
```

前者是 Workflow 责任，后者是 Outcome 责任。两者可以独立失败，因此必须拆成两条 Requirement。

### 8.2 Merge Test

同时满足以下条件时，优先合并 A 与 B：

1. 它们在可观察层面始终一起成功或失败；
2. 单独记录任一项都不会增加新的诊断信息。

合并不得隐藏不同来源、能力边界、`evaluation_type` 或独立失败模式。如果合并会遮蔽其中任一信息，就应保留为独立 Candidate。

### 8.3 Delete / Demote Test

删除一个 Candidate 不会失去任何独立的可观察失败模式，并且它只是实现细节、示例、背景说明、其他 Requirement 中的细碎步骤或不增加规范性责任的重复表述时，应删除或降级为 note。

不得仅因为一条 Candidate 难以测试就删除它。如果它确属 normative 且在范围内，应保留为待澄清项或留给后续 Contract Design。

## 9. Outcome / Workflow 分类

只保留：

```text
outcome
workflow
```

不得新增 `constraint`、`mixed` 或第三种 Requirement 类别。

### 9.1 Outcome

当责任主要根据最终输出或最终状态判断时，使用 `outcome`。例如：“最终输出不得包含敏感字段。”

### 9.2 Workflow

当责任主要根据执行轨迹、动作、顺序、工具调用、授权、禁止行为或中间步骤判断时，使用 `workflow`。例如：“Agent 不得修改用户原文件。”

禁止行为和约束不是第三类。禁止某个动作通常是 `workflow`；禁止最终结果具有某种属性通常是 `outcome`。

### 9.3 混合陈述

如果一句话同时包含 Outcome 与 Workflow 责任，应用 Split Test。当两者可以独立失败时，分别建立 Candidate，后续形成独立 Requirement。不得使用 `mixed`。

## 10. 冲突处理

当两个适用的 Normative Source 要求不兼容的责任时，构成规范冲突：

```text
Source A → 要求 X
Source B → 要求 Y
X 与 Y 无法同时满足
```

Agent 不得根据偏好、当前实现或便利性自行选择一边。

Candidate Ledger 必须把受影响 Candidate 标记为 `CONFLICT`，并保留：

- 两个来源；
- 不兼容的内容；
- 受影响的能力或范围；
- 对 Requirement Extraction 的影响；
- 已知的来源优先级规则，但不得自行发明规则。

未解决的规范冲突不能伪装成已确定 Requirement 进入 Final Requirement Set。必须由人工决定或适用的更高优先级规则解决。如果冲突阻塞对 Skill 的可靠理解，Pass 1 必须输出 `UNDERSTANDING_BLOCKED`。

实现差异不自动等于两个 Normative Source 之间的冲突。除非该实现资源已被明确委托规范权威，否则应单独记录。

## 11. 不确定 Candidate

Collect 阶段偏 recall。可能责任具有合理规范依据，但其含义、范围、权威或粒度不确定时，先保留 Candidate 并记录不确定原因。

产生 Final Requirement Set 前，每一个不确定 Candidate 必须得到以下处置之一：

- `keep`；
- `merge`；
- `remove`；
- `note`；
- `conflict / needs clarification`。

不得通过直接分配正式 Requirement ID 来掩盖不确定性。只有来源成立且问题已解决的 Candidate 才能进入最终 Requirement。

## 12. Final Requirement Set

Final Requirement Set 只使用已经冻结的 Requirement Schema，不增加字段：

| 字段 | 必填 | 规则 |
|---|---:|---|
| `requirement_id` | 是 | 当前 Benchmark 内稳定的 ID，例如 `R001` |
| `statement` | 是 | 清楚表达一项评估责任 |
| `source` | 是 | `skill`、`user`、`project`、`interface` 或 `other` |
| `source_ref` | 否 | 存在稳定位置时记录简短、可追溯的来源位置 |
| `evaluation_type` | 是 | `outcome` 或 `workflow` |

原文摘录、status、notes、不确定项和冲突细节只保留在 Candidate Ledger 或 Traceability Review 中，不得加入冻结的 Requirement 对象。

最终 Requirement 必须同时满足：

- 表达规范性责任，而不只是当前 Implementation Fact；
- 具有合法来源并能够回溯；
- 属于当前 Eval 范围；
- 不是未解决冲突或未解决不确定项；
- 不只是背景、示例或细碎实现步骤；
- 其粒度保留了具有独立意义的可观察失败；
- 分类为 `outcome` 或 `workflow`；
- 后续能够进入 Contract Design，且没有嵌入 Grader assertion。

## 13. Decision Checklist

完成 Requirement Extraction 前逐项检查：

- [ ] 我是否理解了整个 in-scope Skill？
- [ ] 这是规范性责任还是实现细节？
- [ ] 是否有合法来源？
- [ ] 是否需要读取被引用或被委托的资源？
- [ ] 是否包含多个可独立失败的责任？
- [ ] 是否应该拆分？
- [ ] 是否可以与其他 Candidate 合并且不损失诊断价值？
- [ ] 是否只是细碎实现步骤、示例或背景说明？
- [ ] 是 `outcome` 还是 `workflow`？
- [ ] 是否存在适用来源之间的冲突？
- [ ] 是否有已识别的规范内容被遗漏且没有明确处置？
- [ ] 最终 Requirement 是否都能回溯来源？

只有 Skill Summary、Requirement Candidate Ledger、Traceability Review 和 Final Requirement Set 全部存在，并且 Checklist 没有未解释的失败时，Requirement Extraction 才完成。
