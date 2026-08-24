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

## 4. Reading Scope：为 Pass 1 建立可靠整体理解

### 4.1 `SKILL.md` 是入口，但不一定是完整规范

Pass 1 从 Target Skill 的主入口规范开始，例如 `SKILL.md`。正常阅读流程是：

```text
主入口规范
→ 理解整体任务与正式行为
→ 识别被引用或委托的必要资源
→ 按需读取会影响 Skill Understanding 的资源
→ 建立可靠的整体理解
```

Agent 应先理解 Skill 的整体任务和正式行为，再识别主规范引用或委托的必要资源。只有当资源会影响下列任一方面时，才继续读取：

- 正式行为；
- 输出；
- workflow；
- validation；
- authorization；
- forbidden actions；
- failure handling；
- completion condition。

不得机械读取整个目录。普通 assets、生成文件、无关示例、测试、缓存和内部 helper 不会自动进入阅读范围。一个实现文件仅仅存在，不代表它的实现细节属于正式规范。

### 4.2 规范性依赖判断

符合以下任一条件时，应读取被引用或委托的资源：

- 主规范声明该资源定义必需行为或输出；
- Skill 要求 Agent 遵循该资源；
- Skill 要求结果符合该资源；
- 该资源影响 workflow、validation、authorization、forbidden actions、failure handling 或 completion condition；
- 理解某个 capability / task branch 或必需工作流离不开该资源；
- 该资源可能包含相互冲突的规范性指令；
- 不读取它就无法可靠完成 Pass 1。

读取一个资源，不代表其中所有内容都自动具有规范性。Agent 必须判断规范委托了什么责任，以及哪些内容与该委托有关。

### 4.3 Capability Map 与复杂 Skill 的覆盖方式

Capability Map 是 Pass 1 的阅读辅助产物，用于防止复杂 Skill 的整个能力区域在后续 Candidate Collection 中被遗漏。它：

- 不是 Framework Core Object；
- 不是 Schema；
- 不是所有 Skill 都必须复杂生成的正式对象；
- 不预定义任何 capability taxonomy。

具体 capability 名称必须来自 Target Skill 本身，不得由 Framework 写死。对于复杂 Skill，Agent 应先识别：

- shared / cross-cutting responsibilities；
- 每一个主要 capability / task branch；
- 分支特有的依赖、输入、输出与约束；
- 明确不在范围内的能力或分支。

简单 Skill 可以只记录一个主 capability 和少量 shared responsibilities。成功理解一个路径，不能证明已经理解整个复杂 Skill。

## 5. Normative Source 与 Implementation Fact

### 5.1 Normative Source

Normative Source 用于理解“Skill 被要求怎样工作”，例如：

- 主规范，例如 `SKILL.md`；
- 被 Skill 明确指定为正式标准的 reference；
- 最终结果必须符合的 schema；
- Skill 必须运行或通过的 validator；
- 必须遵循的 checklist；
- 必须使用的 template；
- 具有正式约束作用的 config；
- 用户明确要求；
- 项目或接口正式要求。

Pass 1 只识别这些来源、理解其委托范围并记录它们对 Skill Understanding 的影响，不在本阶段生成 Requirement、Requirement Candidate 或正式 ID。

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

Implementation Fact 不得自动覆盖 Normative Source，也不得在 Pass 1 自动生成后续 Requirement。Pass 1 发现两者不一致时，只记录 mismatch 及其影响。

### 5.3 对资源的规范委托

script、schema、validator、template、reference 或 config，只有在 Normative Source 明确委托的范围内才成为正式标准的一部分。例如：

- “必须运行 validator X”委托了执行该 validator 的要求；
- “最终结果必须符合 schema Y”委托了 schema Y 中适用的输出规则；
- “必须使用 template Z”委托了该 template 所规定的结构或内容；
- “reference A 定义正式输出规范”委托了该 reference 中的输出规范。

Agent 必须把被委托资源读取到足以理解被委托责任的程度。同一资源中的无关实现细节不会自动变成 Requirement。

### 5.4 规范与实现不一致

当 Normative Source 与 Implementation Fact 不一致时：

- 保留 Normative Source 的正式含义；
- 将实现差异记录为 implementation mismatch；
- 不得静默用当前实现覆盖规范；
- 不得在 Pass 1 决定后续 Requirement；
- 没有后续阶段的运行证据时，不得声称实现满足规范。

## 6. 四遍 Requirement Extraction 流程

四遍流程各有不同目标。不得把它们压缩成从原文直接生成正式 Requirement ID 的一次转换。

### 6.1 Pass 1 — Understand

**唯一目标：**在开始 Requirement Candidate Extraction 前，建立对 Target Skill 的可靠整体理解。

Pass 1 回答：

> 这个 Skill 是什么、能做什么、怎么工作、依赖什么、哪些地方还不清楚？

Pass 1 不负责生成 Requirement、`RC-xxx`、`R001`、Contract、Test Case 或 Grader，也不负责打分。

#### Pass 1 应回答的问题

Pass 1 至少应回答：

1. Skill 的核心目的是什么？
2. 输入是什么？
3. 输出或最终完成状态是什么？
4. 正常成功执行的大致流程是什么？
5. Skill 提供哪些主要能力或任务分支？
6. 哪些规则是跨能力共享的？
7. 它依赖哪些重要资源、工具、schema、validator 或 config？
8. 哪些依赖具有规范性？
9. 有哪些明显的 outcome constraints、workflow constraints、validation rules、authorization rules、forbidden actions、failure handling 和 completion conditions？
10. 有哪些规范冲突、歧义、缺失信息或 implementation mismatch？

#### 执行步骤

1. 从 Target Skill 的主入口规范开始，例如 `SKILL.md`。
2. 理解整体任务、正式行为、输入、输出和完成状态。
3. 识别 shared responsibilities 和主要 capability / task branches。
4. 识别 Normative Source、Implementation Fact 以及主规范引用或委托的必要资源。
5. 按 Reading Scope 只读取会影响可靠理解的资源。
6. 记录已理解的约束类别、排除项、冲突、歧义、缺失信息和 implementation mismatch。
7. 判断当前信息是否足以进入 Requirement Candidate Collection。

#### Pass 1 必需产物

Pass 1 完成后必须产生：

1. **Skill Summary**：简洁复述整个 Skill，包括核心目的、输入、输出或最终完成状态，以及主要能力边界。
2. **Normal Execution Flow**：描述典型成功路径及理解整体行为所需的主要分支。
3. **Capability Map**：列出 shared / cross-cutting responsibilities 与主要 capability / task branches；简单 Skill 可以非常简短，甚至只记录一个主 capability。
4. **Important Dependencies**：对每项重要 dependency / resource，记录为什么需要读取、是否 normative，以及它影响哪部分理解。
5. **Known Constraints**：只记录理解到的约束类别和内容，不在本阶段把它们正式转换为 Requirement。
6. **Uncertainties / Conflicts**：记录 normative conflict、ambiguity、missing information 和 implementation mismatch，并说明其影响。
7. **Understanding Status**：只能是 `UNDERSTANDING_READY` 或 `UNDERSTANDING_BLOCKED`。

#### READY / BLOCKED

`UNDERSTANDING_READY` 表示当前信息足以进入 Requirement Candidate Collection。READY 不要求 Skill 完全没有歧义；只要核心目的清楚、能力边界基本清楚、主要规范来源已识别，并且已知冲突已显式记录，即可 READY。

`UNDERSTANDING_BLOCKED` 表示当前信息不足以可靠判断 Skill 的核心任务、规范来源、主要输入输出或关键能力边界。此时必须记录每个阻塞原因及其影响，不继续 Requirement Candidate Extraction，也不得假设缺失区域没有 Requirement。

#### Pass 1 Completion Gate

进入 Pass 2 前确认：

- [ ] 能准确复述 Skill
- [ ] 已识别输入和输出
- [ ] 已识别主要正常流程
- [ ] 已识别主要 capability / task branches
- [ ] 已识别 shared responsibilities
- [ ] 已区分 Normative Source / Implementation Fact
- [ ] 已读取必要的委托资源
- [ ] 已记录关键约束
- [ ] 已记录冲突和不确定项
- [ ] 状态为 `UNDERSTANDING_READY`

### 6.2 Pass 2 — Collect

**目标：**基于 Pass 1 已建立的 Skill Understanding，尽可能完整地收集所有可能构成 Requirement 的规范性责任。

Pass 2 的核心原则是 **Recall first**：先尽量找全，再由 Pass 3 判断如何拆分、合并、删除、降级或调整粒度。Pass 2 不负责把 Candidate 整理成 Final Requirement Set。

#### Pass 2 输入与进入条件

Pass 2 使用 Pass 1 的全部产物：

- Skill Summary；
- Normal Execution Flow；
- Capability Map；
- Important Dependencies；
- Known Constraints；
- Uncertainties / Conflicts；
- `UNDERSTANDING_READY` 状态。

如果 Pass 1 状态为 `UNDERSTANDING_BLOCKED`，不得进入 Pass 2。不得用不完整的 Candidate Collection 绕过尚未建立的 Skill Understanding。

#### 按区域和规范维度扫描

Pass 2 不预设具体 capability taxonomy。Agent 必须依据 Pass 1 动态识别出的下列区域逐一扫描：

- shared / cross-cutting responsibilities；
- 每一个 in-scope capability / task branch。

对每个区域，都检查下列通用规范维度：

- required outcomes；
- output constraints；
- required workflow；
- preconditions；
- required tools / resources；
- ordering；
- authorization；
- forbidden actions；
- conditional behavior；
- validation；
- retry / recovery；
- failure handling；
- stop conditions；
- completion conditions。

这些只是防止遗漏的扫描维度，不是 Requirement 类型，也不要求每个区域在每个维度下都产生 Candidate。最终 `evaluation_type` 仍只有 `outcome` 或 `workflow`。

#### Candidate 纳入边界

Candidate 必须有规范性责任作为依据。可能成为 Candidate 的内容包括：

- 必须产生某个结果；
- 必须满足某项输出约束；
- 必须执行某个流程或使用某项正式工具 / 资源；
- 必须先满足前置条件或取得授权；
- 不得执行某个行为；
- 某个条件发生时必须采取某项动作；
- 必须执行 validation；
- 失败后必须停止、重试、恢复或报告；
- 只有达到某个状态才能宣布完成。

下列内容不得自动升级为 Candidate：

- 背景说明；
- 示例；
- ordinary implementation detail；
- helper function 行为；
- 当前代码偶然采用的实现方式；
- 未被规范委托的 script 内部机制；
- Agent 自己认为“最好应该这样”的行为。

Implementation Fact 可以帮助定位或理解可能责任，但不能独立支持 Candidate。若无法找到规范性依据，应记录为 note 或 implementation mismatch，而不是创建 Requirement Candidate。

#### Recall-first 记录策略

当一项可能责任具有合理的规范性依据，但其含义、范围、权威或粒度暂时不确定时，先记录 Candidate，并标记状态和原因。Pass 2 优先避免 false negative，不因暂时拿不准而提前丢弃。

真正的 merge、remove、demote 和 granularity normalization 留给 Pass 3。Pass 2 只允许为了忠实表达原规范，将一句明显包含两个完全不同责任的陈述初步记录为两个 Candidate；这不代表最终粒度已经确定。

#### Candidate Statement

每条 `candidate_statement` 应：

- 忠实于 Normative Source；
- 表达一项可能的责任；
- 不直接复制大段原文；
- 不擅自加强、缩小或补全规范；
- 不提前写入 Grader assertion 或具体评分逻辑。

来源原文应以最小但足以审查的上下文保存在 `source_excerpt`，而不是全部塞入 Candidate Statement。

#### Tentative Evaluation Type

Pass 2 可以把 `tentative_evaluation_type` 暂定为：

- `outcome`：主要依据最终输出或最终状态判断；
- `workflow`：主要依据执行轨迹、动作、顺序、工具调用、授权或禁止行为判断。

这只是暂定分类。无法可靠暂定时可以记录为未决定并说明原因；Pass 3 必须允许重新分类。

#### 冲突、不确定项与实现差异

如果两个适用的 Normative Source 互相冲突，不得选边。将相关记录标记为 `CONFLICT`，并保留 Source A、Source B、各自要求、不兼容内容以及对后续 Extraction 的影响。

如果是 Normative Source 与 Implementation Fact 不一致，应记录 `IMPLEMENTATION_MISMATCH`，保留规范要求、当前实现事实、差异和影响。不得把同一项 mismatch 伪装成两个互相竞争的 Requirement Candidate。

如果规范意义、范围或权威暂时不清楚，将 Candidate 标记为 `UNCERTAIN`，并记录不确定原因和需要澄清的内容。

#### Pass 2 Coverage Check

Pass 2 结束前执行轻量 Collection Coverage Check：

1. Capability Map 中每一个 in-scope capability / task branch 都已扫描；
2. shared / cross-cutting responsibilities 已扫描；
3. 每个区域都检查过全部通用规范维度；
4. 没有整个 capability / task branch 无故遗漏。

该检查只证明 Collection 的区域和扫描维度已覆盖，不判断 Candidate 是否应保留、如何规范化，也不是 Pass 4 Traceability Review。

#### Pass 2 必需输出

Pass 2 必须产生：

1. **Requirement Candidate Ledger**：记录全部 Candidate、来源、状态和审查上下文；它是必需中间产物，不是 Frozen Requirement Schema。
2. **Collection Coverage**：至少记录已扫描的 capabilities / task branches、shared areas、Candidate 数量以及是否存在明显空白。
3. **Conflicts / Uncertainties**：汇总所有 `CONFLICT`、`UNCERTAIN` 和 `IMPLEMENTATION_MISMATCH` 记录。
4. **Collection Status**：只能是 `COLLECTION_READY` 或 `COLLECTION_BLOCKED`。

`COLLECTION_READY` 表示 Pass 1 为 `UNDERSTANDING_READY`，所有 in-scope 区域已完成扫描，且已知冲突、不确定项和实现差异均被显式记录。它不表示 Candidate 已规范化或已成为 Requirement。

`COLLECTION_BLOCKED` 表示至少一个 in-scope 区域因缺失或不可访问的规范来源、无法判定的扫描边界或其他明确阻塞而无法完成可靠收集。必须记录阻塞区域、原因和影响，不得以局部 Candidate 集合宣布 READY。

#### Pass 2 Completion Gate

进入 Pass 3 前确认：

- [ ] Pass 1 状态为 `UNDERSTANDING_READY`
- [ ] 所有 in-scope capability / task branches 已扫描
- [ ] shared / cross-cutting responsibilities 已扫描
- [ ] 每个 Candidate 都有 Normative Source
- [ ] 来源上下文足以供人工审查
- [ ] 冲突未被擅自解决
- [ ] Implementation Fact 未被自动升级为 Candidate 或 Requirement
- [ ] 未分配 `R001` 等正式 Requirement ID
- [ ] Collection Coverage 与 Conflicts / Uncertainties 已完成
- [ ] 状态为 `COLLECTION_READY`

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

Candidate Ledger 是 Pass 2 必需、可审查的中间产物。它是 Extraction 工作记录，不是 Frozen Requirement Schema，也不会为冻结的 Requirement 对象增加字段。

至少在概念上记录：

| 字段 | 用途 |
|---|---|
| `candidate_id` | Pass 2 使用的临时 ID，例如 `RC-001`；不得使用 `R001` 等正式 ID |
| `candidate_statement` | 当前可能责任的陈述 |
| `capability / scope` | shared area、capability / task branch 或其他适用范围 |
| `tentative_evaluation_type` | 暂定的 `outcome` 或 `workflow`；Pass 2 可以未决定 |
| `source` | 规范来源类别，例如 `skill`、`user`、`project`、`interface` 或 `other` |
| `source_ref` | 可追溯的规范来源位置 |
| `source_excerpt` | 人工审查所需的最小原文上下文 |
| `status` | Pass 2 使用 `CANDIDATE`、`UNCERTAIN` 或 `CONFLICT`；后续阶段可按其规则更新 |
| `notes` | 不确定原因、冲突关系、初步粒度说明或其他审查上下文 |

Candidate Ledger 可以为一条 Candidate 保留多个规范来源，尤其是来源共同支持同一责任或彼此冲突时。这样做不会修改最终 Requirement Schema。

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

实现差异不自动等于两个 Normative Source 之间的冲突。除非该实现资源已被明确委托规范权威，否则应标记为 `IMPLEMENTATION_MISMATCH`，记录规范要求、实现事实、差异和影响；不得据此构造两个互相竞争的 Requirement Candidate。

## 11. 不确定 Candidate

Collect 阶段偏 recall。可能责任具有合理规范依据，但其含义、范围、权威或粒度不确定时，先保留 Candidate，将其标记为 `UNCERTAIN`，并记录不确定原因。

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
