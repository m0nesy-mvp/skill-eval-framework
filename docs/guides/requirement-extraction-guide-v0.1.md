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
3. **Normalized Candidate Set**：Pass 3 完成来源、粒度、类型和 contractability 审查后的候选集合；
4. **Candidate Disposition Matrix**：Pass 3 对每条原始 Candidate 去向的完整审计记录；
5. **Traceability Review**：Pass 4 的 Trace Run Metadata、Source Trace Inventory、Forward / Backward Trace Matrices、Trace Issues、Trace Review、Finalization Eligibility Summary 和 Trace Status；
6. **Finalization Mapping**：保留 eligible Normalized Candidate 到 Frozen Requirement 的确定性投影与审计关系；
7. **Final Requirement Set**：只包含已接受 Requirement，并使用冻结的 Requirement Schema。

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

### 4.3 Normative Source Inventory

Normative Source Inventory 是 Pass 1 的明确中间产物，用于在 Requirement Candidate Collection 前回答：哪些资源为什么具有规范性，以及其规范范围是什么。

它不是 Framework Core Object，不是 Schema，也不会修改最终 Requirement Schema。每个 source entry 至少记录：

| 字段 | 用途 |
|---|---|
| `resource` | 文件、章节、用户要求、项目要求、接口或其他来源 |
| `source_type` | `skill`、`user`、`project`、`interface` 或 `other` |
| `authority_basis` | 为什么该资源可以约束 Target Skill |
| `delegation_basis` | 如果权威来自其他规范的引用或委托，记录该关系 |
| `normative_scope` | 该资源约束整体 Skill、某 capability、某输出、某 workflow、某 schema / validation 或其他范围 |
| `read_reason` | 为什么必须读取该资源才能形成可靠理解 |
| `access_status` | 已读取、不可访问、缺失或其他影响理解的状态 |
| `notes` | 局部规范性、实现信息、歧义或其他审查上下文 |

读取过一个文件，不等于整个文件都是 Normative Source。同一文件可以在一个明确范围内具有规范性，同时在其他部分只包含 Implementation Fact、current-state information、背景或示例。Inventory 必须按适用部分和 `normative_scope` 记录，不能把文件级访问自动升级为文件级权威。

### 4.4 Capability Map 与复杂 Skill 的覆盖方式

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

### 5.4 Normative Rule Resolution

当两个规范规则看起来存在差异时，不得直接按文件类型、文件名或固定层级决定权威。Agent 应按以下顺序判断它们属于 compatible、scoped exception、ambiguity 还是真正的 conflict：

1. 检查是否存在明确的 authority 或 delegation 声明。
2. 检查两个规则是否作用于同一个 scope、对象、条件和阶段。
3. 如果规则可以同时满足，将其记录为 compatible。
4. 如果 general rule 明确允许或随后定义了一个限定范围的 exception，将该规则记录为 scoped exception，不自动记为 `CONFLICT`。
5. 如果两个适用的规范规则作用于同一 scope、要求互不兼容，并且没有明确 authority、delegation 或 exception 关系可以解决，记录 `CONFLICT`。
6. 如果现有信息不足以判断是 scoped exception、ambiguity 还是真正冲突，建立 `UNCERTAIN` extraction issue，不得静默选边。

Agent 不得仅因为当前实现如此、某条规则更方便、某个文件更新时间更新，或主观认为某种安排更合理，就自行提升规范权威。Guide 不建立类似“主规范永远高于 reference”或“schema 永远高于 prose”的固定文件优先级；权威必须来自实际声明、委托关系和适用范围。

### 5.5 规范与实现不一致

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
5. 建立 Normative Source Inventory，记录每项来源的权威、委托关系、规范范围、读取理由和访问状态。
6. 按 Reading Scope 只读取会影响可靠理解的资源。
7. 按 Normative Rule Resolution 判断 compatible、scoped exception、ambiguity 和 conflict。
8. 记录已理解的约束类别、排除项、冲突、歧义、缺失信息和 implementation mismatch。
9. 判断当前信息是否足以进入 Requirement Candidate Collection。

#### Pass 1 必需产物

Pass 1 完成后必须产生：

1. **Skill Summary**：简洁复述整个 Skill，包括核心目的、输入、输出或最终完成状态，以及主要能力边界。
2. **Normal Execution Flow**：描述典型成功路径及理解整体行为所需的主要分支。
3. **Capability Map**：列出 shared / cross-cutting responsibilities 与主要 capability / task branches；简单 Skill 可以非常简短，甚至只记录一个主 capability。
4. **Normative Source Inventory**：记录规范来源的 authority、delegation、normative scope、读取理由和访问状态，并允许一个资源只有部分内容具有规范性。
5. **Important Dependencies**：对每项重要 dependency / resource，记录为什么需要读取、是否 normative，以及它影响哪部分理解。
6. **Known Constraints**：只记录理解到的约束类别和内容，不在本阶段把它们正式转换为 Requirement。
7. **Uncertainties / Conflicts**：记录 normative conflict、ambiguity、missing information 和 implementation mismatch，并说明其影响。
8. **Understanding Status**：只能是 `UNDERSTANDING_READY` 或 `UNDERSTANDING_BLOCKED`。

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
- [ ] Normative Source Inventory 已记录 authority、delegation、scope 和 access status
- [ ] 已读取必要的委托资源
- [ ] 已区分 compatible、scoped exception、ambiguity 和 true conflict
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
- Normative Source Inventory；
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
- completion conditions；
- orchestration / state handoff；
- ownership / cleanup boundary。

这些只是防止遗漏的扫描维度，不是 Requirement 类型，也不要求每个区域在每个维度下都产生 Candidate。最终 `evaluation_type` 仍只有 `outcome` 或 `workflow`。

`orchestration / state handoff` 用于检查一个 capability 的结果是否必须交给下一个 capability、required state transition、status file / state object、chaining prerequisite，以及 success / failure branch handoff。

`ownership / cleanup boundary` 用于检查 artifact 的创建者或归属、允许修改或删除的文件、必须保留的内容、cleanup scope、destructive action boundary，以及 ownership 无法确认时的处理。

这两个维度不会产生新的 `evaluation_type`。相关责任最终仍只能归入 `outcome` 或 `workflow`。

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

Pass 2 的 `tentative_evaluation_type` 只能是：

```text
outcome | workflow | undetermined
```

`undetermined` 表示当前 Collection 证据不足以可靠暂定为 `outcome` 或 `workflow`。它只允许存在于 Pass 2；Pass 3 必须重新判断，正式 Requirement 不允许使用 `undetermined`。

#### 冲突、不确定项与实现差异

Pass 2 不把所有问题塞进 Requirement Candidate 的单值 `status`。`CONFLICT`、`UNCERTAIN` 和 `IMPLEMENTATION_MISMATCH` 必须记录到独立的 Extraction Issue Ledger，并通过 Candidate IDs 与相关 Candidate 建立多对多关联。

如果两个适用的 Normative Source 在执行 Normative Rule Resolution 后仍构成 true conflict，不得选边。建立 `CONFLICT` issue，保留双方来源、各自要求、不兼容内容以及对后续 Extraction 的影响。

如果是 Normative Source 与 Implementation Fact 不一致，应建立 `IMPLEMENTATION_MISMATCH` issue，保留规范要求、当前实现事实、差异和影响。Implementation mismatch 本身不是 Requirement Candidate，不得把同一项 mismatch 伪装成两个互相竞争的 Candidate。

如果规范意义、范围或权威暂时不清楚，建立 `UNCERTAIN` issue，记录不确定原因和需要澄清的内容。相关 Candidate 保留在 Candidate Ledger，并通过 issue 关联，而不是依赖单值 status 同时表达所有问题。

#### Pass 2 → Pass 1 回退规则

Pass 2 不是不可回退的线性流程。Collect 过程中发现新的理解缺口时，按其影响处理：

- 如果只是某条规范语义暂不确定、某个非核心责任缺少信息，或某个 Candidate 的边界不清，记录 `UNCERTAIN` issue，并继续扫描其他可理解区域。
- 如果新信息会推翻或显著改变 Skill 核心目的、capability boundary、主要 input / output、关键 Normative Source authority，或整个区域的理解，停止受影响区域的 Collection，回到 Pass 1 更新 Skill Understanding、Capability Map 和 Normative Source Inventory。
- 如果回到 Pass 1 后能够补足理解，再从受影响区域继续 Collect；不得假装此前 Candidate 未受影响。
- 如果无法补足，输出 `COLLECTION_BLOCKED`，记录阻塞区域、原因和影响。

不得为了维持线性流程而禁止回退，也不得仅因局部非核心不确定项就把整个 Collection 自动判为 blocked。

#### Pass 2 Coverage Matrix

Pass 2 结束前必须建立轻量的二维 Collection Coverage Matrix：

```text
Capability / Scope × Generic Collection Dimension
```

每个 cell 至少使用以下状态之一：

| Cell status | 含义 | 必需记录 |
|---|---|---|
| `scanned` | 已执行检查的过程标记，可与更具体的结果状态一起使用 | 可记录简短说明 |
| `candidate_found` | 已发现一个或多个 Candidate | Candidate IDs |
| `none_found` | 已检查，未发现规范性责任 | 原因 |
| `not_applicable` | 该维度不适用于此 scope | 原因 |
| `blocked` | 该 cell 因来源、访问或理解问题无法完成扫描 | 阻塞原因和影响 |

Coverage Matrix 必须覆盖 Capability Map 中每一个 in-scope capability / task branch、shared / cross-cutting responsibilities，以及所有 Generic Collection Dimensions。不得以某个区域 Candidate 数量较少为理由省略整行，也不得用自然语言总结代替未填 cell。

完成 Coverage Check 时，每个未被标记为 `blocked` 的 cell 都必须能够回答“发现了 Candidate、没有发现责任，还是该维度不适用”；不能只保留 `scanned` 而不记录检查结果。

该 Matrix 只检查 Collection completeness 的区域级覆盖，不判断 Candidate 是否应保留、如何规范化，也不建立 Normative Source 与最终 Requirement 的双向追溯，因此不是 Pass 4 Traceability Review。

#### Pass 2 必需输出

Pass 2 必须产生：

1. **Requirement Candidate Ledger**：记录全部 Candidate、多来源证据、相关 extraction issues 和审查上下文；它是必需中间产物，不是 Frozen Requirement Schema。
2. **Extraction Issue Ledger**：独立记录 `CONFLICT`、`UNCERTAIN` 和 `IMPLEMENTATION_MISMATCH`，并关联相关 Candidate 与来源。
3. **Collection Coverage Matrix**：记录每个 capability / scope 与每个通用扫描维度的 cell 状态、Candidate IDs 或原因。
4. **Collection Status**：只能是 `COLLECTION_READY` 或 `COLLECTION_BLOCKED`。

`COLLECTION_READY` 表示 Pass 1 为 `UNDERSTANDING_READY`，所有 in-scope 区域已完成扫描，且已知冲突、不确定项和实现差异均被显式记录。它不表示 Candidate 已规范化或已成为 Requirement。

`COLLECTION_BLOCKED` 表示至少一个 in-scope 区域因缺失或不可访问的规范来源、无法判定的扫描边界或其他明确阻塞而无法完成可靠收集。必须记录阻塞区域、原因和影响，不得以局部 Candidate 集合宣布 READY。

#### Pass 2 Completion Gate

进入 Pass 3 前确认：

- [ ] Pass 1 状态为 `UNDERSTANDING_READY`
- [ ] 所有 in-scope capability / task branches 已扫描
- [ ] shared / cross-cutting responsibilities 已扫描
- [ ] 每个 Candidate 都有 Normative Source
- [ ] 每个 Candidate 的多来源证据均逐项配对且足以供人工审查
- [ ] 冲突未被擅自解决
- [ ] 所有 `CONFLICT`、`UNCERTAIN` 和 `IMPLEMENTATION_MISMATCH` 已进入 Extraction Issue Ledger
- [ ] Implementation Fact 未被自动升级为 Candidate 或 Requirement
- [ ] 未分配 `R001` 等正式 Requirement ID
- [ ] Coverage Matrix 的所有 in-scope cells 均有状态、Candidate IDs 或原因
- [ ] 新发现的核心理解缺口已按规则回退 Pass 1 或明确阻塞
- [ ] 状态为 `COLLECTION_READY`

### 6.3 Pass 3 — Normalize

**目标：**把 Pass 2 的高召回 Requirement Candidate Ledger 整理为语义清晰、来源支持、粒度合理、重复受控、类型明确、冲突保留，并能够进入 Pass 4 Trace 的 Normalized Candidate Set。

Pass 3 回答：

> 我们找出来的 Candidate 应该如何组织成合理的 Requirement 候选？

Pass 3 不负责检查整个规范是否已被完整覆盖，不分配正式 `R001` ID，不冻结 Final Requirement Set，也不进行 Contract 或 Grader 设计。Normative Source → Requirement 的 source-level completeness 属于 Pass 4 Trace。

#### Pass 3 输入与进入条件

Pass 3 只能在 Pass 2 状态为 `COLLECTION_READY` 时开始。输入至少包括：

- Requirement Candidate Ledger；
- Collection Coverage Matrix；
- Normative Source Inventory；
- Extraction Issue Ledger；
- Pass 1 的 Skill Understanding artifacts。

如果 Pass 2 为 `COLLECTION_BLOCKED`，不得开始 Normalize，也不得用局部 Candidate 集合替代完整输入。

#### Normalize 基本原则

Pass 2 采用 Recall first；Pass 3 转向 **Precision + Diagnostic Value**。Agent 不再因“可能有用”而无条件保留 Candidate，而要判断它是否值得成为独立、可诊断的 Requirement 候选。

不得为了减少数量而人为合并。粒度必须由规范语义、适用 scope 和独立失败模式决定，不能由目标数量、缩减比例或版面长度决定。合法的 SPLIT 与 MERGE 可能相互抵消，Normalized Candidate 数量不是成功指标。

#### Candidate Dispositions

Pass 3 必须为每一条 Pass 2 Candidate 给出一个明确的 `primary_disposition`：

```text
KEEP
KEEP_WITH_EDIT
SPLIT
MERGE
REMOVE
DEMOTE_TO_NOTE
CONFLICT
NEEDS_CLARIFICATION
```

| Primary disposition | 含义 |
|---|---|
| `KEEP` | 原 Candidate 的责任、粒度和 wording 可直接进入 Normalized Candidate Set |
| `KEEP_WITH_EDIT` | 责任成立，但需收缩加强语义、澄清 wording、修正 scope 或去除实现偶然性 |
| `SPLIT` | Candidate 包含多个可以独立失败且值得分别诊断的责任 |
| `MERGE` | 多个 Candidate 表达同一责任或可观察意义上基本同真同假 |
| `REMOVE` | 无规范支持、重复后无独立价值、仅为实现事实或不属于 Requirement 候选 |
| `DEMOTE_TO_NOTE` | 对理解有帮助，但不是独立规范责任，应保留为审查说明 |
| `CONFLICT` | 相关 true conflict 在 Normative Rule Resolution 后仍未解决 |
| `NEEDS_CLARIFICATION` | 规范责任可能存在，但当前语义、scope、权威或失败含义仍不足以正常化 |

每条原始 Candidate 都必须有去向。不得静默丢失、覆盖或仅从 Normalized Candidate Set 中省略 Candidate。

一个 Candidate 在 Normalize 中可能同时发生多个变化，因此 disposition record 不得假设一个枚举值能够表达全部处理过程：

- `primary_disposition` 表示该 Candidate 最主要的最终处置，仍使用上表 vocabulary；
- `secondary_transformations` 是可选列表，记录同时发生的其他结构变化或审计事实；只有单一动作时可以为空。

`secondary_transformations` 可以记录 `edited`、`merged_with`、`split_into`、`evidence_consolidated`、`child_demoted`、`scope_narrowed`、`reclassified` 等简短动作及其目标或关联 ID。该列表是 Candidate-level audit information，不是 Framework Core Object，也不修改 Final Requirement Schema。具体序列化格式本 Guide 不冻结，但每项 transformation 必须能够从 rationale、目标 IDs 和来源关系中得到解释。

#### Disposition Precedence

当多个 disposition 同时适用时，先判断 unresolved semantic state：

1. 存在 unresolved true conflict 时，`primary_disposition` 为 `CONFLICT`；
2. 不存在 unresolved true conflict，但仍有无法消除的 semantic gap 时，`primary_disposition` 为 `NEEDS_CLARIFICATION`。

在这两种情况下，同时发生的 `SPLIT`、`MERGE`、`KEEP_WITH_EDIT`、`DEMOTE_TO_NOTE` 或其他结构变化记录到 `secondary_transformations` 和 rationale，不得用结构动作掩盖 unresolved state。如果 true conflict 与 semantic gap 同时存在，`CONFLICT` 优先，semantic gap 仍通过 issue 关联和 rationale 保留。

如果不存在 unresolved issue，再根据实际结构处置选择 `SPLIT`、`MERGE`、`KEEP_WITH_EDIT`、`KEEP`、`REMOVE` 或 `DEMOTE_TO_NOTE` 作为 `primary_disposition`。Precedence 只解决主处置的表达顺序，不是数值评分体系，也不改变各项 disposition 的适用条件。

#### `REMOVE` 与 `DEMOTE_TO_NOTE`

`REMOVE` 表示 Candidate 不应继续存在于 Requirement Extraction 结果中。典型原因包括：

- 没有 Normative Source 支持；
- 完全是 Implementation Fact 或错误推断；
- 与保留 Candidate 完全重复，且没有额外审查价值；
- 是没有独立意义的过度碎片。

`REMOVE` 不产生 Normalized Candidate，也不要求把内容作为正式 note 保留；Candidate Disposition Matrix 仍必须记录删除原因。

`DEMOTE_TO_NOTE` 表示内容不应成为 Requirement，但对理解、审查、风险判断或后续设计仍有价值，例如 informative background、implementation caveat、non-normative recommendation、useful design context、current-state limitation 或 contextual explanation。

`DEMOTE_TO_NOTE` 不产生 Normalized Candidate，但内容及其来源应进入 normalization notes 或其他 audit notes。不得仅因为内容“看起来有用”就让它继续作为 Requirement 候选；是否降级取决于它没有独立规范责任、但仍具有明确审查价值。

#### Normalize 处理顺序

对每条 Candidate 及其相关 Candidate 集合依次执行：

1. Normative Support Check；
2. Atomic Responsibility Test；
3. Merge Test；
4. Parent / Child Rule；
5. Over-fragmentation Test；
6. Statement Normalization；
7. Outcome / Workflow Final Classification；
8. Contractability Check；
9. Conflict、Uncertainty 和 Implementation Mismatch 关联审查；
10. Multi-source evidence consolidation；
11. 在 Candidate Disposition Matrix 中记录 `primary_disposition`、适用的 `secondary_transformations` 和目标关系，并生成或更新 Normalized Candidate。

处理顺序是审查路径，不代表每一步都必须改变 Candidate。任何 SPLIT、MERGE、REMOVE 或 wording 修改都必须保留原 Candidate、来源证据和 extraction issue 的可追溯关系。

#### Pass 3 必需输出

Pass 3 必须产生：

1. **Normalized Candidate Set**：使用临时 `NR-` ID，记录通过 Normalize 的候选责任及其来源、类型、派生关系和 issue 关联。
2. **Candidate Disposition Matrix**：确保每条原始 `RC-` Candidate 都有 `primary_disposition`、适用的 `secondary_transformations`、目标 Normalized Candidate 或无目标原因。
3. **Normalization Status**：只能是 `NORMALIZATION_READY` 或 `NORMALIZATION_BLOCKED`。

#### Pass 3 Completion Gate

进入 Pass 4 前确认：

- [ ] Pass 2 状态为 `COLLECTION_READY`
- [ ] 每个 `RC-` Candidate 都有 `primary_disposition`
- [ ] 同时发生的额外结构变化已记录到 `secondary_transformations` 或明确为空
- [ ] 没有静默丢失 Candidate
- [ ] 所有 Normalized Candidate 都有 Normative Source 支持
- [ ] 需要 clause-to-evidence mapping 的 multi-source Candidate 已完成映射
- [ ] 无规范支持的加强语义已删除
- [ ] duplicate Candidate 已处理
- [ ] composite responsibility 已执行 Atomic Responsibility Test
- [ ] parent / child 与 over-fragmentation 已检查
- [ ] 每条 Normalized Candidate 的 `evaluation_type` 已最终确定为 `outcome` 或 `workflow`
- [ ] 没有 `undetermined`
- [ ] unresolved true conflict 保持 `CONFLICT`
- [ ] unresolved semantic gap 标记为 `NEEDS_CLARIFICATION`
- [ ] 每条 `NORMALIZED` Candidate 都具备继续 Contract 化的潜力
- [ ] 已生成 Candidate Disposition Matrix
- [ ] 未分配 `R001` 等正式 Requirement ID

全部满足时输出 `NORMALIZATION_READY`。如果存在无法给出处置的 Candidate、无法完成类型终判、关键来源问题未被正确保留，或其他条件导致 Normalized Candidate Set 不可进入 Pass 4，则输出 `NORMALIZATION_BLOCKED`，并记录原因和影响。

### 6.4 Pass 4 — Trace

**目标：**对已经完成 Normalize 的 Requirement 候选执行最终的双向规范追溯审计，确认每一项应覆盖的 Normative Responsibility 都有明确去向，并确认每一条 Normalized Candidate 的全部实际规范语义都有充分来源支持。

Pass 4 本质上审查：

```text
Normative Source Responsibilities
↕
Normalized Candidate Set
```

Pass 4 必须确认：

1. 所有应被 Requirement Extraction 覆盖的规范责任都有明确去向；
2. 所有 Normalized Candidate 的实际规范语义都有充分 Normative Source 支持；
3. 没有遗漏规范责任；
4. 没有无来源或来源不足的候选责任；
5. unresolved conflict / clarification 被完整保留，而不是伪装成普通 Requirement。

Pass 4 是 audit stage，不负责重新设计 Requirement。它只能在 Pass 3 状态为 `NORMALIZATION_READY` 时开始；如果 Pass 3 为 `NORMALIZATION_BLOCKED`，不得用局部或不稳定的 Normalized Candidate Set 开始 Trace。

Pass 4 至少使用：

- Normative Source Inventory；
- Skill Understanding artifacts；
- Requirement Candidate Ledger；
- Extraction Issue Ledger；
- Normalized Candidate Set；
- Candidate Disposition Matrix；
- `source_evidence`；
- 存在时的 `statement_clauses` 和 clause-to-evidence mapping。

Pass 4 还必须为本次审计建立 Trace Run Metadata，把上述输入绑定到同一个确定的 source snapshot。Metadata 至少记录 run identifier、target identifier、source snapshot identity、可用的 revision / hash / immutable identifier、snapshot timestamp，以及本次使用的 Guide version / revision。Source system 不必是 Git repository；只要能够明确“本轮审计针对哪个确定版本”即可。

Pass 4 审查两个方向：

```text
Source Trace Item → Normalized Candidate / Issue / Exclusion
Normalized Candidate / clause → Source Trace Item / Source Evidence
```

详细规则见“Pass 4 Traceability Audit”。Pass 4 必须产生 Trace Run Metadata、Source Trace Inventory、Forward Trace Matrix、Backward Trace Matrix、Trace Issues、Trace Review、Finalization Eligibility Summary 和 Trace Status。状态只能是：

```text
TRACE_READY
TRACE_READY_WITH_UNRESOLVED_ISSUES
TRACE_BLOCKED
```

`TRACE_READY` 和 `TRACE_READY_WITH_UNRESOLVED_ISSUES` 都表示双向 trace 已完整；二者只在 unresolved semantic state 是否仍阻止相关责任 finalization 上不同。`TRACE_BLOCKED` 表示 trace 不完整、输入无效或必须回退前序 Pass。

#### Pass 4 Completion Gate

结束 Pass 4 前确认：

- [ ] Pass 3 状态为 `NORMALIZATION_READY`
- [ ] Trace Run Metadata 已把全部 Trace artifacts 绑定到同一个 source snapshot
- [ ] Source Trace Inventory 已建立
- [ ] 所有 Trace Items 都有且只有一个 Forward Trace 主结果
- [ ] 没有 Trace Item 被静默遗漏
- [ ] 所有 Normalized Candidates 都完成 Backward Trace
- [ ] 需要 clause-level trace 的 Candidate 已逐 clause 审计
- [ ] 每个 `EXCLUDED` Trace Item 都有 source evidence、exclusion category、rationale、authority / delegation assessment 和 reviewer-visible note
- [ ] unresolved `CONFLICT` / `NEEDS_CLARIFICATION` 有完整 Issue linkage
- [ ] `TRACE_GAP` 已显式报告
- [ ] `PARTIALLY_SUPPORTED` / `UNSUPPORTED` 已显式报告
- [ ] Finalization Eligibility Summary 已逐项覆盖全部 Normalized Candidates
- [ ] 本轮 Trace artifacts 未因输入或 source snapshot 变化而 stale
- [ ] Pass 4 没有新建、删除、拆分、合并或改写 Candidate / Normalized Candidate
- [ ] Pass 4 没有自行解决 conflict 或改变 scope / `evaluation_type`
- [ ] 未分配 `R001` 等正式 Requirement ID
- [ ] 未进入 Contract Design

## 7. Pass 2 Working Ledgers

### 7.1 Requirement Candidate Ledger

Candidate Ledger 是 Pass 2 必需、可审查的中间产物。它是 Extraction 工作记录，不是 Frozen Requirement Schema，也不会为冻结的 Requirement 对象增加字段。

至少在概念上记录：

| 字段 | 用途 |
|---|---|
| `candidate_id` | Pass 2 使用的临时 ID，例如 `RC-001`；不得使用 `R001` 等正式 ID |
| `candidate_statement` | 当前可能责任的陈述 |
| `capability / scope` | shared area、capability / task branch 或其他适用范围 |
| `tentative_evaluation_type` | `outcome`、`workflow` 或仅限 Pass 2 的 `undetermined` |
| `source_evidence` | 一个或多个相互配对的规范来源证据项 |
| `related_issue_ids` | 与 Candidate 相关的零个或多个 Extraction Issue ID |
| `status` | Candidate 的工作状态；Pass 2 通常为 `CANDIDATE`，不再承担所有 issue 分类 |
| `notes` | 初步粒度、边界或其他审查上下文 |

一个 Candidate 可以由多个 Normative Source 支持。`source_evidence` 在概念上是列表，每个 evidence entry 至少包含：

| 字段 | 用途 |
|---|---|
| `source` | `skill`、`user`、`project`、`interface` 或 `other` |
| `source_ref` | 该项证据自己的可追溯来源位置 |
| `source_excerpt` | 与该 `source_ref` 成对的最小审查上下文 |
| `authority / delegation reference` | 需要时指向 Normative Source Inventory 中的权威或委托依据 |

每一段 `source_ref` 必须与自己的 `source_excerpt` 成对保存，不能把多个来源位置和多个摘录分别堆进两个无对应关系的列表。具体序列化格式本轮不冻结，但这种配对关系是必需的。

多来源 Candidate、`source_evidence` 和 `related_issue_ids` 只完善 Candidate / Extraction audit information，不修改冻结的 Final Requirement Schema。最终 Requirement 仍只使用既有的 `source` 和可选 `source_ref` 字段。

拆分 Candidate 时，每个结果都必须保留适用的来源追溯。合并 Candidate 时，合并记录必须保留足以支持合并陈述的全部来源。

### 7.2 Extraction Issue Ledger

Extraction Issue Ledger 是 Pass 2 的独立中间产物，用于记录 Candidate Collection 中发现的问题。它不是 Framework Core Object，不是 Requirement Schema，也不自动产生 Requirement。

至少记录以下 issue type：

```text
CONFLICT | UNCERTAIN | IMPLEMENTATION_MISMATCH
```

每条 issue 至少包含：

| 字段 | 用途 |
|---|---|
| `issue_id` | 临时稳定 ID，例如 `EI-001` |
| `issue_type` | `CONFLICT`、`UNCERTAIN` 或 `IMPLEMENTATION_MISMATCH` |
| `scope` | 受影响的 shared area、capability、输出、workflow 或其他范围 |
| `related_candidate_ids` | 零个或多个相关 Candidate；Implementation mismatch 可以没有 Candidate |
| `related_sources` | 与问题相关且保持各自引用关系的规范来源或实现事实 |
| `description` | 问题本身，不替代 Candidate Statement |
| `impact` | 对理解、Collection、后续阶段或可执行性的影响 |
| `resolution_status` | 未解决、已澄清、已按正式规则解决或其他明确状态 |
| `notes` | 需要的补充审查上下文 |

同一个 Candidate 可以关联多个 issue，同一个 issue 也可以影响多个 Candidate。Candidate Ledger 与 Issue Ledger 通过 IDs 关联，不依赖一个 Candidate `status` 同时表达冲突、不确定性和实现差异。

`IMPLEMENTATION_MISMATCH` 本身不是 Requirement Candidate。只有存在独立 Normative Source 支持的责任才能进入 Candidate Ledger；当前实现事实只进入 issue 的 `related_sources` 和审查说明。

## 8. Pass 3 Normalize Rules

### 8.1 Normative Support Check

Normalize 首先确认 Candidate 是否有足够的 Normative Source 支持。至少检查：

- `candidate_statement` 是否忠实于自己的 `source_evidence`；
- 是否加入来源没有要求的限定条件、质量属性、范围或完成条件；
- 是否把 Implementation Fact 当成规范；
- 是否把 example、recommendation、explanation 或背景当成硬要求；
- 多个来源是否真的支持同一责任，而不是碰巧使用相似词语；
- authority、delegation 和 normative scope 是否覆盖 Candidate 当前表达的责任。

如果 Candidate 只有 Implementation Fact 支持，使用 `REMOVE`；如果该信息仍有助于理解或后续审查，使用 `DEMOTE_TO_NOTE`。Implementation mismatch 本身仍不得成为 Requirement 候选。

如果规范责任成立，但 Candidate wording 加入了没有来源支持的强化语义，使用 `KEEP_WITH_EDIT`，删除或收缩超出来源的部分。例如，来源只要求产生某个目标产物，Candidate 不得自行增加“非空”“通过某项校验”或其他没有独立规范依据的条件。

### 8.2 Atomic Responsibility Test

Atomicity 不由动词数量、句子长度、标点或 bullet 数量决定。对于 Candidate 中可能包含的责任 A 和 B，先检查：

1. A 是否可以满足而 B 不满足，或 B 可以满足而 A 不满足；
2. 这两种失败是否产生可区分、值得独立记录的评估结论。

技术上能够独立成功或失败，只是 SPLIT 的必要信号，不是充分条件。继续执行 Diagnostic Value Review：

1. 两种失败是否指向不同的 failure cause 或 failure class？
2. 两种失败是否通常需要不同的 remediation 或 correction？
3. 分开记录是否会改变后续诊断、风险判断或修复决策？

只有独立失败并且分开记录能够保留实际 diagnostic value 时，才使用 `SPLIT`。如果 A 与 B 理论上可以分别失败，但根因相同、修复方式相同，且分开记录不会改变任何后续决策，通常不应只因技术可分而拆分。

Artifact package、metadata block、正式结构中的普通字段以及 checklist micro-items 不因各组成项可以单独缺失就自动拆分。除非某个组成项被规范独立强调，或其失败具有不同 failure class、remediation、风险或决策影响，否则应把它保留在能够表达完整责任的合理粒度中。

如果只是同一责任的自然组成动作，或拆开后不会增加诊断价值，不因文字结构机械拆分，也不建立数值评分或 diagnostic threshold。

抽象地说，“必须执行规定的验证，并且最终结果必须满足该验证要求”可能包含两个可独立失败的责任：执行验证属于 workflow，最终结果满足要求属于 outcome。是否拆分仍取决于实际 Normative Source 是否分别支持这两个责任。

### 8.3 Merge Test

多个 Candidate 满足以下任一情形时，考虑 `MERGE`：

- 表达同一规范责任；
- 只是不同来源对同一责任的重复支持；
- 只是语义等价的改写；
- 在可观察评估意义上基本同真同假，独立评分不会增加有价值的失败结论。

判断核心是 diagnostic value，而不是措辞相似度。MERGE 不得隐藏不同 scope、不同 `evaluation_type`、独立失败模式、独立授权边界或具有单独意义的来源强调。

合并后必须保存所有适用的 `source_evidence`、`related_issue_ids` 和原 Candidate 关系。Normalized Candidate 的 `derived_from_candidate_ids` 必须包含全部被合并 Candidate。不存在 unresolved semantic state 时，Candidate Disposition Matrix 对每条原 Candidate 记录 `MERGE` 作为 `primary_disposition` 并指向同一个目标 `NR-` ID；存在 unresolved state 时，按 Disposition Precedence 记录主处置，并把 merge 写入 `secondary_transformations`。

### 8.4 Parent / Child Rule

当一个 Candidate 表达整体约束，另一个 Candidate 只表达其中一个细节约束时，不得默认把每个普通组成部分都保留为独立 Requirement 候选。

如果 child responsibility 只是 parent responsibility 的普通组成部分，且删除独立 child 不会失去新的失败模式或诊断价值，通常使用 `MERGE`、`REMOVE` 或 `DEMOTE_TO_NOTE`。

只有当 child responsibility 满足至少一项时，才考虑独立保留：

- 被 Normative Source 独立强调；
- 失败具有独立的业务、安全、权限、数据完整性或其他实质意义；
- 与 parent 可以独立成功或失败；
- 需要形成独立评估结论才能保留有价值的诊断信息。

正式 schema、checklist、template 或 validator 包含很多细项，不代表每个普通字段或步骤都必须成为独立 Candidate。是否独立保留仍由规范强调和失败意义决定。

### 8.5 Over-fragmentation Test

如果一个 Candidate 只是另一责任的低层实现动作、顺序中的细碎步骤或无独立意义的机械分片，并且删除它不会失去独立规范失败模式，则使用 `REMOVE` 或 `DEMOTE_TO_NOTE`。

例如，如果正式责任是完整读取一个输入资源，就不应仅因执行过程涉及多个局部读取动作而机械生成多个 Requirement 候选，除非某个局部动作被规范独立强调并具有独立失败意义。

不得仅因为 Candidate 难以测试就删除它。如果它确属 normative，但当前 wording、scope 或失败含义不足，应使用 `KEEP_WITH_EDIT` 或 `NEEDS_CLARIFICATION`。

### 8.6 Statement Normalization

每条 `normalized_statement` 应满足：

- 只表达一个主要责任；
- 语义明确且忠实于 Normative Source；
- 不包含当前实现的偶然细节，除非该实现已在适用 scope 内被正式委托；
- 不加入 Grader、Test Case、Metric、threshold、regex、checker 或具体 assertion；
- 不使用无法定位所指对象的模糊代词；
- 不使用“正确处理”“合理完成”“表现良好”等没有可审查含义的表述；
- 保持足够稳定，使后续能够进行 Contract Design。

如果 Normative Source 本身只提供无法进一步明确的模糊表达，不得由 Agent 自行发明精确含义。保留最忠实的语义，并使用 `NEEDS_CLARIFICATION`。

### 8.7 Contractability Check

Pass 3 不写 Contract，但每条状态为 `NORMALIZED` 的 Candidate 必须具备被 Contract 化的潜力。判断问题是：

> 如果违反这条责任，能否描述一种具有独立意义的可观察失败？

Pass 3 只要求能够描述“违反这条责任时会出现什么类型的可观察失败”。此处不要求定义 threshold、metric、regex、checker、reference answer、grading algorithm 或其他 Contract / Grader 细节。能够描述 failure class，不等于已经完成 Contract 设计。

如果连失败类型都无法描述，说明 statement 仍太模糊、粒度不合理，或 Normative Source 信息不足，应继续 Normalize 或标记 `NEEDS_CLARIFICATION`。

Contractability 不等于已经可自动测试，也不要求在 Pass 3 选择验证方法。

### 8.8 Multi-source Normalization

一个 Normalized Candidate 可以由多个 Normative Sources 支持。Normalize 时必须：

- 合并完全重复的 source evidence entry；
- 为每个需要被引用的 evidence entry 分配 Candidate-local `evidence_id`；
- 保留每个 `source_ref` 与自己的 `source_excerpt` 配对；
- 保留需要的 authority / delegation context；
- 不把多个来源压缩成无法追溯的单一字符串；
- 确认每项 evidence 支持 Normalized statement 的适用部分。

如果多个来源只是重复支持同一责任，应形成一个 Normalized Candidate，并通过 `derived_from_candidate_ids` 和完整 `source_evidence` 保留来源与 Candidate 历史。

如果一个 `normalized_statement` 包含多个具有实际规范语义的 clause，并且没有同一个 source evidence 完整支持这些 clause，必须建立 clause-to-evidence mapping。概念结构为：

```text
statement_clauses:
  - clause_id
  - clause_text
  - supporting_evidence_ids

source_evidence:
  - evidence_id
  - source
  - source_ref
  - source_excerpt
```

`supporting_evidence_ids` 必须指向同一 Normalized Candidate 中实际存在的 evidence entries，并足以支持对应 clause。需要时，evidence entry 继续保留 authority / delegation reference。

如果一个来源已经完整支持整个 statement，不强制建立 `statement_clauses`。不得按连词、标点或普通语法片段机械拆 clause；只有具有实际规范语义、且其来源支持不同的部分才需要映射。Clause-to-evidence mapping 是 Pass 3 audit information，不是 Framework Core Object，也不修改 Final Requirement Schema。

## 9. Outcome / Workflow Final Classification

Pass 2 的 `tentative_evaluation_type` 在 Pass 3 必须重新判断。Normalized Candidate 的 `evaluation_type` 只能是：

```text
outcome | workflow
```

`undetermined` 不能进入 Normalized Candidate Set 的 `NORMALIZED` 状态，也不得成为正式 Requirement 类型。不得新增 `constraint`、`mixed` 或任何第三种最终类别。

### 9.1 Outcome

当责任主要通过最终输出或最终状态判断时，分类为 `outcome`。

### 9.2 Workflow

当责任主要通过执行轨迹、动作、顺序、工具使用、授权、禁止行为或中间步骤判断时，分类为 `workflow`。

禁止行为和约束不是第三类。禁止某个动作通常属于 `workflow`；禁止最终结果具有某种属性通常属于 `outcome`。

### 9.3 Outcome / Workflow Composite

如果一个 Candidate 同时包含 Outcome 与 Workflow，执行 Atomic Responsibility Test。两项责任能够独立失败且分别具有诊断价值时，使用 `SPLIT`，生成分别分类为 `outcome` 和 `workflow` 的 Normalized Candidate。不能使用 `mixed` 逃避粒度判断。

如果两部分只是同一责任不可分离的表达，应根据主要判定对象选择一个类型，并在 normalization rationale 中解释，而不是机械拆分。

## 10. Extraction Issue Handling in Pass 3

### 10.1 Conflict Handling

Pass 3 不得擅自解决 unresolved true conflict。如果 Extraction Issue Ledger 中的 `CONFLICT` 在再次执行 Normative Rule Resolution 后仍无法消解：

- 相关 Candidate 使用 `CONFLICT` 作为 `primary_disposition`；
- 对应 Normalized Candidate 状态保持 `CONFLICT`；
- 保留 `related_issue_ids`、双方来源和影响；
- 不强制合并成一个正常 Candidate；
- 不根据当前实现、便利性或时间戳选择一方。

如果 Pass 3 确认原 issue 实际属于 compatible rules、scoped exception 或不同 scope，可以按正式 authority、delegation 和 scope 关系解除 conflict，但必须在 Extraction Issue Ledger 中记录 resolution rationale、更新 `resolution_status`，并在 normalization rationale 中说明对 Candidate 的影响。

### 10.2 Uncertainty Handling

对于 `UNCERTAIN` issue，Pass 3 应根据现有来源选择明确处置：

- 现有 evidence 足够支持责任：正常化为 `KEEP` 或其他适用 disposition；
- wording 可通过收缩或澄清恢复忠实性：`KEEP_WITH_EDIT`；
- 只是有用说明而非规范责任：`DEMOTE_TO_NOTE`；
- 没有 Normative Source 支持：`REMOVE`；
- 仍缺少决定责任、scope、权威或失败含义的信息：`NEEDS_CLARIFICATION`。

不得让模糊的 uncertainty 无解释地进入 Pass 4。每个相关 issue 的 resolution status、处置理由和 Candidate 影响都必须记录。

### 10.3 Implementation Mismatch

Implementation mismatch 本身仍不得成为 Requirement Candidate，也不得改变 Normative Source 的正式含义。Normalized Candidate 可以继续关联相关 `IMPLEMENTATION_MISMATCH` issue，以保留当前实现差异和后续审查上下文。

如果 Candidate 只有 Implementation Fact 支持，使用 `REMOVE` 或 `DEMOTE_TO_NOTE`；如果 Candidate 有独立规范支持，则按规范正常化，并保留 mismatch issue 关联。Pass 3 不修复实现，也不根据 mismatch 改写规范责任。

## 11. Pass 3 Output Artifacts

### 11.1 Normalized Candidate Set

Normalized Candidate Set 使用临时 ID：

```text
NR-001
NR-002
...
```

不得使用正式 `R001`、`R002`。每条 Normalized Candidate 至少记录：

| 字段 | 用途 |
|---|---|
| `normalized_id` | Pass 3 临时 ID，例如 `NR-001` |
| `normalized_statement` | Normalize 后的单一主要责任陈述 |
| `evaluation_type` | 只能是 `outcome` 或 `workflow` |
| `capability_or_scope` | 适用的 shared area、capability、task branch 或其他 scope |
| `source_evidence` | 成对保留 `evidence_id`、引用与摘录的一个或多个 Normative Source evidence |
| `statement_clauses` | 仅在多个实际语义 clause 由不同 evidence 支持时记录 clause-to-evidence mapping；其他情况可省略 |
| `derived_from_candidate_ids` | 产生该记录的全部原始 `RC-` Candidate IDs |
| `related_issue_ids` | unresolved issue、已解决 issue 或 relevant mismatch 的关联 IDs |
| `disposition_summary` | 汇总产生该结果的 `primary_disposition` 与适用的 `secondary_transformations` |
| `normalization_rationale` | 来源支持、粒度、类型、wording 和 issue 处理理由 |
| `status` | `NORMALIZED`、`CONFLICT` 或 `NEEDS_CLARIFICATION` |

`NORMALIZED` 表示该 Candidate 已通过 Pass 3 的来源、粒度、类型、statement 和 contractability 检查，可以进入 Pass 4。`CONFLICT` 和 `NEEDS_CLARIFICATION` 保留问题状态，不得伪装成可直接进入 Final Requirement Set 的正常 Candidate。

Normalized Candidate Set 不是 Final Requirement Set，不修改 Frozen Requirement Schema，也不证明 source-level completeness。

### 11.2 Candidate Disposition Matrix

Candidate Disposition Matrix 是 Pass 3 的必需审计产物，用于证明每一条原始 Candidate 都有明确去向。至少记录：

| 字段 | 用途 |
|---|---|
| `candidate_id` | 原始 `RC-` ID |
| `primary_disposition` | 最主要的最终处置：`KEEP`、`KEEP_WITH_EDIT`、`SPLIT`、`MERGE`、`REMOVE`、`DEMOTE_TO_NOTE`、`CONFLICT` 或 `NEEDS_CLARIFICATION` |
| `secondary_transformations` | 可选列表；记录同时发生的 edit、merge、split、evidence consolidation、child demotion、scope narrowing、reclassification 等额外变化；无额外变化时为空 |
| `normalized_target_ids` | 零个、一个或多个目标 `NR-` IDs |
| `rationale` | 处置原因，包括来源、粒度、重复、类型或 issue 判断 |

Primary disposition、secondary transformations 与目标关系必须清楚：

```text
一个 RC → primary SPLIT → 多个 NR
多个 RC → primary MERGE → 一个 NR
一个 RC → primary REMOVE / DEMOTE_TO_NOTE → 无 NR，并记录原因
一个 RC → primary KEEP / KEEP_WITH_EDIT → 一个 NR
一个 unresolved RC → primary CONFLICT / NEEDS_CLARIFICATION → 零个或多个问题状态 NR，并在 secondary transformations 中记录同时发生的结构变化
```

`primary_disposition` 只能有一个；`secondary_transformations` 可以有零个或多个，但不得用它们替代主处置或隐藏 unresolved semantic state。Matrix 不得省略被删除、降级、冲突或待澄清的 Candidate。`derived_from_candidate_ids` 与 Matrix 应能相互核对，但这种 Candidate-level disposition 审计不是 Pass 4 的 source-level completeness Trace。

### 11.3 Pass 3 与 Pass 4 的边界

Pass 3 主要处理：

```text
Candidate → Normalized Candidate
```

它可以读取 Candidate 已保存的 source evidence 核对语义，但不重新逐句扫描原始规范以证明没有遗漏。以下问题属于 Pass 4：

```text
Normative Source → Requirement completeness
```

Pass 3 不分配正式 Requirement ID，不冻结 Final Requirement Set，也不把 Candidate Disposition Matrix 当作 Traceability Review。

## 12. Pass 4 Traceability Audit

### 12.1 Pass 2 Collection Coverage 与 Pass 4 Trace 的边界

Pass 2 Collection Coverage 是区域级检查，回答：

> 每个 capability / scope 的每个 generic collection dimension 是否已经扫描？

它防止整个区域或某个扫描维度从未被检查。Pass 4 不重复建立 capability / scope × collection dimension Matrix。

Pass 4 Trace 是规范责任级检查，回答：

1. 每一项真正具有规范意义的 source responsibility 最终去了哪里？
2. 每一条 Normalized Candidate 的实际规范语义究竟由哪些 source responsibilities 支持？

因此：

```text
Pass 2 Coverage ≠ Pass 4 Trace
```

Coverage Matrix 完整不能替代 source responsibility-level trace；Trace 完整也不重新证明 Pass 2 的区域扫描过程。

#### Trace Run Metadata 与 Source Snapshot

Pass 4 开始前必须建立最小的 Trace Run Metadata，把本次审计绑定到一个明确的 source snapshot。至少记录：

| 字段 | 用途 |
|---|---|
| `trace_run_id` | 本次 Trace 的 run identifier 或等价审计标识 |
| `target_identifier` | 被审计 Target 的稳定标识 |
| `source_snapshot_id` | 本轮全部 Normative Sources 的统一 snapshot identity |
| `source_revision / source_versions` | Source system 提供时记录 commit、revision、version 或其他稳定 revision；多来源时保持来源与版本对应 |
| `source_hashes / immutable_resource_ids` | 适用且容易获得时，按来源记录 hash、immutable resource identifier 或 snapshot manifest identity |
| `snapshot_timestamp` | Trace 开始所针对 snapshot 的捕获或确认时间 |
| `guide_version / guide_revision` | 本轮采用的 Requirement Extraction Guide 版本或 revision |
| `run_validity` | 当前 run 为有效、`stale` 或 `invalidated`，并在非有效时记录原因 |

Source snapshot identity 不依赖 Git。如果存在稳定 revision，优先记录 revision；如果没有，可以使用 hash、immutable resource identifier、受控导出物或 captured snapshot identity。不能因为 source system 没有 Git history 就省略版本边界。

同一次 Trace run 的 Source Trace Inventory、Forward Trace Matrix、Backward Trace Matrix 和 Finalization Eligibility Summary 必须针对同一个 source snapshot。如果 Trace 期间 Normative Source 发生变化，不得把旧 Matrix 与新 source 混用；应将 run 标记为 `stale` 或 `invalidated`，并重新建立受影响的 Trace artifacts。

Trace Run Metadata 属于 Requirement Extraction audit metadata，不是 Framework Core Object，也不会修改 Frozen Requirement Schema。

### 12.2 Source Trace Item

Pass 4 使用 **Source Trace Item** 作为 source-level audit unit，并使用临时 ID：

```text
TI-001
TI-002
...
```

一个 Source Trace Item 表示：

> 从已识别 Normative Sources 或 delegated resources 中抽取、需要得到明确 trace disposition 的 source-level audit item。

Source Trace Item 可以在审查后确认为 normative responsibility，也可以确认为不应进入 Requirement Set 的 non-requirement source item。前者进入 `MAPPED`、`ISSUE` 或 `TRACE_GAP`；后者只有满足严格 exclusion audit 时才能进入 `EXCLUDED`。因此 `EXCLUDED` 不再与“Normative Trace Item”这一名称产生概念冲突。

Source Trace Item 是 Pass 4 的临时审计结构，不是 Framework Core Object、Frozen Requirement、Contract、Test Case 或 Grader，也不会进入 Frozen Requirement Schema。

#### Trace Item Granularity

Trace Item 不得机械按每一行、每一句、每个 bullet 或每个普通结构字段生成。应按“具有独立规范意义、需要确认其是否被 Requirement 覆盖”来划分。

- 几个 source clauses 共同表达一个不可分割的规范责任时，可以形成一个 Trace Item；
- 一个 source statement 明显包含多个独立规范责任时，可以形成多个 Trace Items；
- 仅因文本形式不同，不得拆分或合并 Trace Item；
- Trace Item 粒度用于发现 source-side omission，不用于在 Pass 4 重新执行 Normalize。

如果一个 Trace Item 内可以清楚识别出多个具有独立 normative meaning 的部分，并且其中一部分已映射、另一部分未映射，说明该 Trace Item 的 source audit granularity 太粗。Pass 4 可以只对 Source Trace Inventory 的 audit unit 重新划分，并重新执行受影响的 Forward Trace，前提是：

- 不修改 Requirement Candidate；
- 不修改、拆分、合并或改写 Normalized Candidate；
- 不执行 Normalize；
- 不改变 Requirement 粒度；
- 重新划分只用于准确表达 source-side coverage。

如果 source responsibility 本身不可合理拆分，而现有 NR 只覆盖其中一部分，则该 Trace Item 必须记录为 `TRACE_GAP`，并在 rationale 中分别记录 `covered_portion` 和 `uncovered_portion`。不得因为存在部分映射就标记为 `MAPPED`。

#### Trace Item Identity 与 Rerun Reconciliation

`TI-` ID 是某一次 Source Trace Inventory 内的审计 identity，不是永久业务 ID。不得假设不同 Trace run 中编号相同的 Trace Item 一定表达同一责任。

当 source snapshot 和 responsibility meaning 均未变化时，实现可以尽量保留稳定的 `TI-` identity，方便 diff 和 review。如果 source 修改造成责任新增、删除、拆分、合并、scope 改变或 normative meaning 改变，则 rerun 必须进行 reconciliation，并至少允许记录：

```text
unchanged
added
removed
superseded
split
merged
changed
```

旧 Trace Item 被替代时，应通过 `previous_trace_item_ids`、`supersedes` 或等价字段保留审计关系，并解释变化原因。Removed item 可以保留在 reconciliation record 中，不要求继续作为当前 Inventory 的 active item。

这些 relation 只用于解释“本次 Trace Item 为什么与上一次不同”，不是 Framework Core Object，也不要求建立复杂版本图。

### 12.3 Source Trace Inventory

Pass 4 首先建立 Source Trace Inventory。每个 Trace Item 至少记录：

| 字段 | 用途 |
|---|---|
| `trace_item_id` | 临时 ID，例如 `TI-001` |
| `source_meaning` | 该 source-level audit item 的含义；确认为 normative 时记录完整 `normative_meaning`，不复制无关长段原文 |
| `source_evidence` | 一个或多个保持引用与摘录配对的来源证据项 |
| `source_evidence[].source` | 该 evidence 的 `skill`、`user`、`project`、`interface` 或 `other` 来源分类 |
| `source_evidence[].source_ref` | 该 evidence 自己的稳定来源位置 |
| `source_evidence[].source_excerpt` | 与该 `source_ref` 成对的最小审查上下文 |
| `source_evidence[].authority / delegation reference` | 需要时记录该 evidence 的权威或委托依据 |
| `normative_scope` | 该责任约束的整体范围、局部范围、条件、阶段、输出或其他适用边界 |
| `related_issue_ids` | 与该责任相关的零个或多个 Extraction Issue IDs |
| `reconciliation_status` | Rerun 时记录 `unchanged`、`added`、`removed`、`superseded`、`split`、`merged` 或 `changed`；首次 run 可为空 |
| `previous_trace_item_ids / supersedes` | Rerun 中存在替代、拆分、合并或变化关系时记录旧 TI identity |
| `status / notes` | Inventory 工作状态、排除上下文、authority 说明或其他审计信息 |

单来源 Trace Item 仍必须记录 `source`、`source_ref` 和 `source_excerpt`；多来源 Trace Item 通过 `source_evidence` 列表重复这组字段。每个 entry 至少保留自己的：

```text
source
source_ref
source_excerpt
authority / delegation reference（需要时）
```

如果一个规范责任由多个来源共同表达，允许一个 Trace Item 保存多来源 evidence，但不得把多个 `source_ref` 和多个 `source_excerpt` 拆成无法对应的列表。重复来源可以合并 evidence entry，不得丢失实际 authority、delegation 或 scope 差异。

Source Trace Inventory 必须基于已识别的 Normative Sources 和 delegated resources 做 source responsibility-level 审查；不能只把 Normalized Candidate 的 statements 反向复制成 Trace Items，否则无法独立发现 source-side omission。

### 12.4 Forward Trace

Forward Trace 执行：

```text
Source Trace Item
→ Normalized Candidate / Issue / Exclusion / Gap
```

核心问题是：

> 每一个 Source Trace Item 最终去了哪里？

每个 Trace Item 必须恰好有一个主 `trace_result`：

| Trace result | 含义 |
|---|---|
| `MAPPED` | Trace Item 的全部 normative meaning 被一个或多个 Normalized Candidates 完整覆盖 |
| `ISSUE` | Trace Item 对应 traceable but unresolved 的 `CONFLICT` 或 `NEEDS_CLARIFICATION`，并正确关联问题状态 Candidate / Extraction Issue |
| `EXCLUDED` | 审查确认该内容不是应进入 Requirement Set 的独立规范责任，并记录合法排除原因 |
| `TRACE_GAP` | 该 Trace Item 确实是规范责任，但没有 Normalized Candidate、Issue 或合法 exclusion 可以解释 |

一个 `MAPPED` Trace Item 可以指向一个或多个 `NR-` IDs；一个 `ISSUE` Trace Item 可以指向问题状态 `NR-`、Extraction Issue，或同时指向两者。Traceable 不等于 resolved。

`MAPPED` 必须表示 Trace Item 的完整 normative meaning 已经被解释。如果只有部分语义得到覆盖，应先按 Trace Item Granularity 规则判断能否重新划分 source audit unit；无法合理拆分时，必须记录 `TRACE_GAP`，并明确 covered 与 uncovered portions，不增加模糊的 partial-mapped 状态。

#### `EXCLUDED` Audit Boundary

`EXCLUDED` 只用于审查后确认不应成为 Requirement 的 source item。每个 `EXCLUDED` item 至少记录：

- source evidence；
- `exclusion_category`；
- `exclusion_rationale`；
- authority / delegation assessment；
- reviewer-visible note。

`exclusion_category` 使用简单、通用的类别：

```text
example
explanatory_context
implementation_fact
non_normative_recommendation
architecture_context
duplicate_source_expression
other
```

使用 `other` 时必须解释具体原因。`duplicate_source_expression` 只有在另一个可审查的 Trace Item 已完整保留相同 normative meaning 和 source relation 时才成立，不能只因为文字相近就排除。

不得因为某项责任难以 Normalize、没有现成 NR、测试困难或执行者认为不重要，就把真正的 normative responsibility 标为 `EXCLUDED`。如果无法确认一个 source item 是否具有规范性，不能 `EXCLUDED`；应关联 `UNCERTAIN` / `NEEDS_CLARIFICATION`，或回退 Pass 1 检查 authority、delegation 和 scope。

发现 `TRACE_GAP` 时，不得在 Pass 4 现场创建新的 Candidate 或 Normalized Candidate。

#### Forward Trace Matrix

Forward Trace Matrix 至少记录：

| 字段 | 用途 |
|---|---|
| `trace_item_id` | 被审计的 `TI-` ID |
| `trace_result` | `MAPPED`、`ISSUE`、`EXCLUDED` 或 `TRACE_GAP` |
| `normalized_candidate_ids` | 相关的零个、一个或多个 `NR-` IDs |
| `related_issue_ids` | 相关的零个或多个 Extraction Issue IDs |
| `covered_portion` | `TRACE_GAP` 且存在部分覆盖时，记录已覆盖语义；其他情况可为空 |
| `uncovered_portion` | `TRACE_GAP` 且存在部分覆盖时，记录未覆盖语义；其他情况可为空 |
| `exclusion_category` | `EXCLUDED` 时必填，其他情况可为空 |
| `exclusion_rationale` | `EXCLUDED` 时必填，其他情况可为空 |
| `authority / delegation_assessment` | `EXCLUDED` 时记录为何 source authority 或 delegation 不使该 item 成为规范责任 |
| `reviewer_visible_note` | `EXCLUDED` 时提供便于复核的简短说明 |
| `rationale` | 映射、问题、排除或 gap 的审计理由 |

Matrix 不得静默跳过 Trace Item。一个 Trace Item 只能有一个主 `trace_result`；其他关联通过 Candidate IDs、Issue IDs 和 rationale 表达。

### 12.5 Backward Trace

Backward Trace 执行：

```text
Normalized Candidate / clause
→ Source Trace Item / Source Evidence
```

它不只检查“是否至少有一个 source”，而是检查：

> Normalized Candidate 的每一项实际规范语义是否都有足够 evidence？

每条 Normalized Candidate 必须得到以下一种 aggregate support result：

| Support status | 含义 |
|---|---|
| `SUPPORTED` | 全部实际规范语义都有充分 Normative Source 支持 |
| `PARTIALLY_SUPPORTED` | 一部分 clause 有来源，但至少一个实际规范 clause 缺少充分支持 |
| `UNSUPPORTED` | Candidate 整体没有足够 Normative Source 支持 |
| `ISSUE_BOUND` | Candidate 处于 `CONFLICT` 或 `NEEDS_CLARIFICATION`，全部相关规范语义可追溯，且 unresolved state 已正确关联 Extraction Issue |

`ISSUE_BOUND` 只能用于 traceable but unresolved 的 Candidate。`CONFLICT` / `NEEDS_CLARIFICATION` 不自动等于 unsupported；同样，它们也不得掩盖实际 support gap。如果问题状态 Candidate 仍有未获支持的 clause，应记录 `PARTIALLY_SUPPORTED` 或 `UNSUPPORTED`，并把 unresolved issue 作为关联信息保留。

#### Clause-level Backward Trace

如果 Normalized Candidate 已有 `statement_clauses` 和 `supporting_evidence_ids`，Pass 4 必须使用它们进行 clause-level audit，并把 evidence 对应到 Source Trace Items。

如果简单 Candidate 的整个 statement 被单一 Trace Item / evidence 完整支持，可以使用 Candidate-level row，不强制拆 clause。

如果 statement 包含多个实际规范语义，则必须确认：

```text
每个实际语义 clause
→ 至少一个足以支持它的 Trace Item / source evidence
```

不得按普通语法片段机械拆 clause。Clause-level audit 的目的，是防止“来源列表很多，但某个实际规范 clause 没有来源支持”。如果任何实际 clause 没有充分支持，Candidate 不得评为 `SUPPORTED`。

#### Backward Trace Matrix

Backward Trace Matrix 至少记录：

| 字段 | 用途 |
|---|---|
| `normalized_id` | 被审计的 `NR-` ID |
| `clause_id` | Clause-level audit 时填写；简单 Candidate-level row 可为空 |
| `supporting_trace_item_ids` | 支持该 Candidate / clause 的一个或多个 `TI-` IDs |
| `support_status` | `SUPPORTED`、`PARTIALLY_SUPPORTED`、`UNSUPPORTED` 或 `ISSUE_BOUND` |
| `related_issue_ids` | 相关的零个或多个 Extraction Issue IDs |
| `rationale` | 支持充分性、缺口或 unresolved state 的理由 |

复杂 Candidate 可以有多条 clause rows，但仍必须能够得出 Candidate-level aggregate result。任何 clause 的 partial / unsupported 不能被其他已支持 clause 抵消。

### 12.6 Traceability Complete 与 Requirement Resolved

必须区分：

```text
Traceability complete
≠ Requirement resolved
```

如果两个适用的 Normative Sources 对同一责任给出互斥规则，只要：

- 双方 source responsibilities 都已形成 Trace Items；
- 都映射到问题状态 Normalized Candidate / Extraction Issue；
- conflict 的来源、scope 和影响被完整保留；

则 traceability 可以完整，但该责任仍未 resolved，不能作为普通 Frozen Requirement 晋升。

因此必须区分：

- **Trace failure**：`TRACE_GAP`、`PARTIALLY_SUPPORTED`、`UNSUPPORTED`、无法完成 Inventory 或无法判断 source authority；
- **Unresolved semantic state**：已完整追溯的 `CONFLICT` 或 `NEEDS_CLARIFICATION`。

后者不一定构成 traceability failure。允许保存已经完全 resolved 且 traceable 的候选，而不因一个局部 unresolved issue 丢弃其他已完成工作。

这要求分别记录：

- **Trace completion**：Forward / Backward Trace 是否完整；
- **Finalization readiness**：所有需要进入 Frozen Requirement Set 的责任是否已经 resolved。

可以存在：

```text
Trace complete
+ Unresolved issues remain
```

但不得把 unresolved issue 伪装成正式 Requirement。

### 12.7 Pass 4 是只读审计阶段

Pass 4 不得：

- 新建 Requirement Candidate；
- 新建 Normalized Candidate；
- split、merge、rewrite 或删除 Normalized Candidate；
- 自行解决 Normative Conflict；
- 改变 Requirement scope；
- 改变 `evaluation_type`；
- 分配正式 `R001` 等 Requirement ID；
- 开始 Contract Design。

发现问题时，Pass 4 只记录审计结果、报告影响并回退到正确前序 Pass。修复后必须重新执行受影响的后续 Pass，不能在旧 Trace Matrix 上局部掩盖变更。

#### Rollback Rules

| 发现 | 回退位置 | 必需处理 |
|---|---|---|
| `TRACE_GAP` | Pass 2 — Collect | 补充遗漏 Candidate，然后重新执行 Pass 3 和 Pass 4 |
| `PARTIALLY_SUPPORTED` / `UNSUPPORTED` NR | Pass 3 — Normalize | 根据来源收缩 wording，或使用 REMOVE、DEMOTE_TO_NOTE、NEEDS_CLARIFICATION、重新分类等合法处置，再重新执行 Pass 4 |
| source authority、delegation、scope 或 capability understanding 本身不可靠 | Pass 1 — Understand | 更新 Normative Source Inventory、authority、scope 和 Skill Understanding，再重新执行后续 Pass |
| 仅存在已完整追溯的 unresolved `CONFLICT` / `NEEDS_CLARIFICATION` | 不自动回退 | 保留 unresolved Extraction Issue，等待 human decision 或 authoritative clarification |

如果 Normalized Candidate Set 本身不稳定或 Pass 3 的必需 artifact 不完整，Pass 4 输出 `TRACE_BLOCKED` 并回退 Pass 3，不得继续拼接 Trace 结果。

#### Trace Run Staleness

Pass 4 artifacts 不是永久有效的。如果以下任何输入发生实质变化，相关 Trace artifacts 必须视为 `stale`，不能沿用旧结论：

- Normative Source snapshot；
- Normative Source authority 或 delegation；
- Normalized Candidate Set；
- Candidate statement 或 statement clauses；
- related unresolved issues。

Staleness 至少影响相关的 Source Trace Inventory、Forward Trace Matrix、Backward Trace Matrix 和 Finalization Eligibility Summary。Agent 必须重新执行受影响的 Trace；不得在修改 NR 后沿用旧 `SUPPORTED`，也不得把不同 snapshot 的局部结果拼接成同一次 Trace run。

如果变化只影响可明确隔离的一部分，允许重建受影响部分，但必须更新 Trace Run Metadata、记录 invalidation scope，并重新检查 aggregate counts、Trace Status 和 overall finalization readiness。无法可靠隔离影响时，整个 Trace run 视为 stale。

### 12.8 Pass 4 必需输出

Pass 4 至少产生：

1. **Trace Run Metadata**：run、target、source snapshot 与 Guide revision 的最小审计身份；
2. **Source Trace Inventory**：`TI-` source-level audit units 及适用的 rerun reconciliation；
3. **Forward Trace Matrix**：Trace Item → NR / Issue / Exclusion / Gap；
4. **Backward Trace Matrix**：NR / clause → Trace Item / source support；
5. **Trace Issues**：汇总 `TRACE_GAP`、`PARTIALLY_SUPPORTED`、`UNSUPPORTED`、unresolved `CONFLICT` 和 unresolved `NEEDS_CLARIFICATION`；
6. **Trace Review**：数量审计、trace completion、finalization readiness 和已知限制；
7. **Finalization Eligibility Summary**：逐项记录 Normalized Candidate 的晋升资格，并给出整体 readiness；
8. **Trace Status**：`TRACE_READY`、`TRACE_READY_WITH_UNRESOLVED_ISSUES` 或 `TRACE_BLOCKED`。

Trace Review 至少记录：

- Trace Item 总数；
- `MAPPED` 数量；
- `ISSUE` 数量；
- `EXCLUDED` 数量；
- `TRACE_GAP` 数量；
- `SUPPORTED` NR 数量；
- `PARTIALLY_SUPPORTED` NR 数量；
- `UNSUPPORTED` NR 数量；
- unresolved `CONFLICT` 数量；
- unresolved `NEEDS_CLARIFICATION` 数量。

这些数量只用于审计集合完整性，不是质量评分，不得设置目标数量、通过比例或缩减指标。

### 12.9 Trace Status

#### `TRACE_READY`

同时满足：

- 所有应审计 Trace Items 都有合法 Forward Trace 结果；
- 所有 Normalized Candidates 都完成充分的 Backward Trace；
- 没有 `TRACE_GAP`；
- 没有 `PARTIALLY_SUPPORTED` 或 `UNSUPPORTED`；
- 没有 unresolved issue 阻止 Requirement finalization。

它表示 trace complete，并且所有有资格进入 Final Requirement Set 的责任已经 resolved。

#### `TRACE_READY_WITH_UNRESOLVED_ISSUES`

同时满足：

- Forward / Backward Trace 都完整；
- 没有 `TRACE_GAP`；
- 没有 `PARTIALLY_SUPPORTED` 或 `UNSUPPORTED`；
- 仍存在已正确追溯的 `CONFLICT` 或 `NEEDS_CLARIFICATION`。

这些 issue 阻止对应责任晋升为正式 Frozen Requirement，但不构成 traceability failure。已 resolved 且 traceable 的候选可以保留为 partial progress；只要仍有影响 benchmark definition 的 unresolved issue，整体 Benchmark / Final Requirement Set 就不得宣称 fully frozen。

#### `TRACE_BLOCKED`

存在以下任一情形时使用：

- `TRACE_GAP`；
- `PARTIALLY_SUPPORTED`；
- `UNSUPPORTED`；
- source authority / delegation / scope 无法可靠判断；
- Source Trace Inventory 无法完成；
- Normalized Candidate Set 或 Pass 3 audit artifacts 不稳定、不完整或相互矛盾。

`TRACE_BLOCKED` 必须记录阻塞项、影响和应回退的 Pass。不得把局部 trace 完整解释为整个 Pass 4 完成。

### 12.10 Final Requirement Finalization Boundary

Pass 4 结束后，不得自动把所有 `NR-` 编号为正式 `R-` Requirement。只有同时满足以下条件的 Normalized Candidate，才具有晋升资格：

```text
status = NORMALIZED
+ Backward Trace = SUPPORTED
+ 没有 unresolved blocking issue
```

状态为 `CONFLICT` 或 `NEEDS_CLARIFICATION` 的 Candidate 不得直接晋升。它们必须保留在 Extraction Issues 和 Trace artifacts 中，等待 authoritative resolution；不得丢失，也不得伪装成普通 Requirement。

#### Finalization Eligibility Summary

Pass 4 必须产生结构化 Finalization Eligibility Summary。它不是 Final Requirement Set，不分配 `R-` ID，也不修改 Frozen Requirement Schema。

Summary 至少逐个覆盖全部 Normalized Candidates：

| 字段 | 用途 |
|---|---|
| `normalized_id` | 被审查的 `NR-` ID |
| `normalization_status` | 当前 `NORMALIZED`、`CONFLICT` 或 `NEEDS_CLARIFICATION` 状态 |
| `backward_trace_status` | `SUPPORTED`、`PARTIALLY_SUPPORTED`、`UNSUPPORTED` 或 `ISSUE_BOUND` |
| `unresolved_issue_ids` | 相关的 unresolved blocking issue IDs；没有时为空 |
| `eligible_for_finalization` | 只能是 `true` 或 `false` |
| `ineligibility_reason` | `false` 时记录具体原因；`true` 时可为空 |

资格规则保持：

```text
normalization_status = NORMALIZED
+ backward_trace_status = SUPPORTED
+ 没有 unresolved blocking issue
→ eligible_for_finalization = true
```

`CONFLICT`、`NEEDS_CLARIFICATION`、`PARTIALLY_SUPPORTED` 和 `UNSUPPORTED` 均必须得到 `eligible_for_finalization = false`。如果整个 Trace 状态为 `TRACE_BLOCKED`，允许某些 NR individually eligible，但 `overall_finalization_ready` 必须为 `false`。

Summary 还必须记录：

- `individually_eligible_count`；
- `individually_ineligible_count`；
- `trace_gap_count`；
- `unresolved_conflict_count`；
- `unresolved_clarification_count`；
- `overall_finalization_ready`。

Individual eligibility 不能抵消 source-side gap，也不能把局部可晋升解释成整个 Final Requirement Set 已经 ready。

`overall_finalization_ready` 只有在 Trace Status 允许 finalization、没有 source-side gap 或 unresolved blocking issue，并且所有计划晋升的 Normalized Candidates 均 individually eligible 时才能为 `true`。

Final Requirement ID assignment 和 freeze 是 Requirement Extraction 的确定性收尾步骤，不是新的 Pass。具体规则见“Final Requirement Finalization”；Pass 4 本身不执行 projection、ID assignment，也不设计 Contract、Test Case、Grader 或后续 Benchmark objects。

Pass 4 的 Trace Run Metadata、Trace Item、rerun reconciliation、Forward Matrix、Backward Matrix、Trace Issues、Trace Review、Finalization Eligibility Summary 和 Trace Status 都是 Requirement Extraction working / audit structures，不是新的 Core Objects，也不会为 Frozen Final Requirement Schema 增加字段。

## 13. Final Requirement Finalization

### 13.1 定位与边界

Final Requirement Finalization 不是 Pass 5，也不负责发现、收集、Normalize、Trace 或修复 Requirement。它只执行：

```text
eligible Normalized Candidate
→ Frozen Requirement
```

Finalization 是确定性收尾步骤，不进行新的语义设计。发现需要重新理解、补充 Candidate、修改 statement、重新分类、补全 trace 或解决 extraction issue 时，必须回到对应 Pass；不得在 Finalization 中现场修复。

### 13.2 Preconditions

只有 Pass 4 已完成且其 Trace artifacts 当前有效时，才考虑 Finalization：

| Trace Status | Finalization behavior |
|---|---|
| `TRACE_READY` | 允许进入完整 Requirement Finalization |
| `TRACE_READY_WITH_UNRESOLVED_ISSUES` | 可以保留 individually eligible、已经 resolved 的 Candidate 及其 projection audit，但 unresolved `CONFLICT` / `NEEDS_CLARIFICATION` 不得晋升；整体 Requirement Set / Benchmark Definition 不得宣称 fully frozen，直到 blocking issues 被解决并重新 Trace |
| `TRACE_BLOCKED` | 禁止执行 Requirement Finalization；可以保留 Finalization Eligibility Summary，但不得把局部 eligible NR 冻结成完整 Requirement Set，也不得宣称 finalization complete |

`TRACE_READY_WITH_UNRESOLVED_ISSUES` 下形成的 eligible projection 只能作为可审查的 partial progress 保留；只要 blocking unresolved issue 仍存在，整体 Finalization Status 必须是 `FINALIZATION_BLOCKED`，不得产出 authoritative、complete Frozen Requirement Set。

### 13.3 Candidate Eligibility

一个 Normalized Candidate 只有同时满足以下全部条件才可晋升：

```text
normalization_status = NORMALIZED
+ backward_trace_status = SUPPORTED
+ eligible_for_finalization = true
+ 没有 unresolved blocking issue
+ Trace artifacts 当前不 stale
+ 当前 normalized_statement / candidate version
   与 Trace 所绑定的 statement / version 一致
```

以下 Candidate 或结果不得晋升：

- `CONFLICT`；
- `NEEDS_CLARIFICATION`；
- `PARTIALLY_SUPPORTED`；
- `UNSUPPORTED`；
- 依赖 stale Trace result 的 Candidate；
- 与 Trace 所审查 statement / version 不一致的 Candidate；
- 受 `TRACE_GAP` 影响、仍属于不完整 extraction result 的 Candidate Set。

Finalization 必须使用 Pass 4 的 Finalization Eligibility Summary，不得在本步骤重新解释 eligibility。

### 13.4 Projection to Frozen Requirement Schema

Frozen Requirement Schema 保持不变：

```text
requirement_id
statement
source
source_ref
evaluation_type
```

NR 到 Requirement 的 projection 规则如下：

| Requirement field | Projection rule |
|---|---|
| `requirement_id` | 按 Requirement ID Assignment 规则确定性分配 |
| `statement` | 直接使用最终、已获 Trace support 的 `normalized_statement`；不得在 Finalization 中 rewrite |
| `evaluation_type` | 直接使用 Normalized Candidate 的最终 `outcome` 或 `workflow`；不得在 Finalization 中重新分类 |
| `source` | 从 authoritative normative provenance 中选择 Frozen Schema 允许的 `skill`、`user`、`project`、`interface` 或 `other`；不得根据 implementation location 猜测 |
| `source_ref` | 按 Primary Provenance Projection 规则选择能够确定定位该 Requirement authoritative meaning 的 primary reference |

如果 `statement` 需要修改或 `evaluation_type` 需要重新分类，回退 Pass 3，并在修改后重新执行 Pass 4。Finalization 不得通过 projection 隐式改变 Requirement 语义。

#### Primary Provenance Projection

Normalized Candidate 可以具有 multi-source 或 clause-level evidence，但 Frozen Requirement Schema 仍只保留单一 `source` 和 `source_ref`。Projection 按以下顺序执行：

1. 从已通过 Backward Trace 的 supporting evidence 中识别 authoritative normative provenance，不考虑仅为 Implementation Fact 的位置。
2. 如果一个 authoritative evidence entry 能完整支持整个 Requirement statement，使用该 evidence 的 source classification 和 stable reference 作为 primary `source` / `source_ref`。
3. 如果 provenance 是 primary rule + explicit delegated resource，选择能够最直接定位 Requirement authoritative meaning 的 primary reference，并在 Finalization Mapping 中保留 authority / delegation chain。不得仅因某个位置更方便访问而选择它。
4. 如果不同、不可删除的 clauses 必须依赖多个独立 Normative Sources 才能获得完整支持，选择其中具有明确 authority、delegation 或最直接规范定位依据的 evidence 作为 primary `source` / `source_ref`；所有 supporting evidence IDs 和 clause-level provenance 必须继续保留在 Finalization Mapping 与 Extraction audit artifacts 中。
5. Frozen Requirement 的单一 `source_ref` 不是完整 provenance graph。完整的 multi-source、clause-level、authority 和 delegation provenance 由 Extraction audit artifacts 负责保存。
6. 如果无法依据 authority、delegation、scope 和 directness 确定合理的 primary `source` / `source_ref`，该 Candidate 的 Finalization 必须 `BLOCKED`，不得任意选择。

当 authoritative source system 本身没有稳定可写入的 reference 时，`source_ref` 可以按 Frozen Schema 保持为空，但 Finalization Mapping 必须记录可审查的 evidence identity、缺少 stable ref 的原因和 primary provenance 决策。无法唯一确定 primary provenance 不属于“没有 stable ref”，仍然必须阻塞。

### 13.5 Finalization Mapping

Finalization 必须保留 Finalization Mapping，至少记录：

| 字段 | 用途 |
|---|---|
| `normalized_id` | 来源 `NR-` ID |
| `requirement_id` | 成功晋升后的 `R-` ID；未晋升时为空 |
| `normalized_statement` | Trace 所支持的最终 normalized statement |
| `requirement_statement` | 实际投影的 Frozen Requirement statement |
| `evaluation_type` | 从 Normalized Candidate 直接投影的 `outcome` 或 `workflow` |
| `source` | 投影后的 Frozen source classification |
| `source_ref` | 投影后的 primary source reference |
| `supporting_source_evidence_ids` | 完整 supporting evidence identity 列表，包括 multi-source / clause-level provenance |
| `related_issue_ids` | 相关 Extraction Issue IDs |
| `ordering_basis` | 本次 Requirement ID 使用的稳定排序依据 |
| `finalization_status` | `FINALIZED`、`NOT_ELIGIBLE` 或 `BLOCKED` |
| `rationale` | Eligibility、projection、primary provenance、阻塞或未晋升原因 |

Mapping 应覆盖本次 Finalization 考虑的全部 Normalized Candidates。`FINALIZED` row 必须恰好关联一个 Requirement；`NOT_ELIGIBLE` 或 `BLOCKED` row 不得分配 `requirement_id`。

Finalization Mapping 保留 `NR → R` 关系和完整 provenance，但不是 Framework Core Object，也不会修改 Frozen Requirement Schema。

### 13.6 Requirement ID Assignment

正式 Requirement ID 使用：

```text
R001
R002
R003
...
```

ID 必须在当前 benchmark 内唯一、确定、可审计，不得依赖随机 LLM 输出顺序。分配顺序为：

1. 使用已经稳定并记录在 Normalized Candidate Set 中的 normalized ordering；
2. 如果多个 Candidate 的 ordering 无法区分，使用已经保存的 extraction ordering；
3. 仍需 deterministic secondary ordering 时，使用稳定的 `normalized_id` 顺序。

不得按照 importance、score、criticality 或 statement alphabetical order 任意重排语义顺序。Finalization Mapping 必须记录使用的 ordering basis。

Requirement Set 尚未 frozen 时，ID 可以在完整 re-finalization 中重新生成。一旦某个 benchmark version 已 frozen，其 Requirement IDs 不得因无关 rerun 被静默重编号。Source 或 Requirement 发生实质变化时，应通过新的 benchmark version 或既有 lifecycle 处理；本 Guide 不建立复杂 ID registry。

### 13.7 Final Requirement Validation

Finalization 完成前至少确认：

- [ ] 所有 `requirement_id` 唯一
- [ ] 所有 `requirement_id` 符合 `R001`、`R002`、… 的正式格式
- [ ] 所有 `statement` 非空，并与已 Trace-supported 的 `normalized_statement` 一致
- [ ] `evaluation_type` 只能是 `outcome` 或 `workflow`
- [ ] `source` 只能是 Frozen Schema 允许的枚举值
- [ ] `source_ref` 满足 Primary Provenance Projection；无 stable ref 时有完整 audit rationale
- [ ] 每个 Requirement 都能回到一个 eligible NR
- [ ] 每个 eligible 且已 finalized 的 NR 恰好映射到一个 Requirement
- [ ] 没有 `CONFLICT` Candidate 被晋升
- [ ] 没有 `NEEDS_CLARIFICATION` Candidate 被晋升
- [ ] 没有 `PARTIALLY_SUPPORTED` / `UNSUPPORTED` Candidate 被晋升
- [ ] 没有 stale Trace result 被使用
- [ ] Finalization Mapping 完整且与 Frozen Requirement Set 一致

任一检查失败都必须阻塞 Finalization；不得使用 quality score、通过比例或人工补分覆盖 validation failure。

### 13.8 Finalization Status

Finalization Status 只能是：

```text
FINALIZATION_READY
FINALIZATION_BLOCKED
```

`FINALIZATION_READY` 表示所有应该进入本次 Frozen Requirement Set 的 eligible Candidates 均已完成 projection、ID assignment 和 validation，没有 blocking unresolved issue，并且完整 Requirement Set 可以正式冻结。

`FINALIZATION_BLOCKED` 表示 Finalization 不能完成，例如：

- Trace Status 不允许完整 finalization；
- primary `source` / `source_ref` 无法可靠决定；
- eligibility 与 Trace artifacts 不一致；
- 使用了 stale artifacts；
- ID 或 projection validation failure；
- 存在 unresolved blocking issue。

Finalization Status 不是 quality score，也不表示实现已经满足 Requirement。

### 13.9 Staleness 与 Rollback

Finalization 不直接修复前序问题：

| 发现 | 回退位置 |
|---|---|
| Statement 或 `evaluation_type` 需要改变 | Pass 3 — Normalize，然后重新 Trace |
| Source trace 不完整 | Pass 4，或按 Pass 4 rollback rule 回到正确前序 Pass |
| Source authority / delegation / scope 有问题 | Pass 1 — Understand |
| 存在 missing normative responsibility | Pass 2 — Collect |

如果 NR、Trace artifacts、related issues 或 source provenance 在 Finalization 后发生实质变化，相关 Finalization Mapping 和 Frozen Requirement Set 必须视为 stale，并重新验证或重新 Finalization。不得沿用旧 eligibility、旧 projection 或旧 Requirement ID mapping 来掩盖变化。

### 13.10 Frozen Requirement 与 Contract Boundary

只有 `FINALIZATION_READY` 时，才能产生正式 Frozen Requirement Set，并把它作为后续 Contract Design 的 authoritative Requirement input。

Contract Design 只消费 Frozen Requirements，不直接把 RC、NR 或 TI 当作 authoritative requirement definition。RC、NR、TI、Trace Matrix 和 Finalization Mapping 可以作为 audit context，但不能替代正式 Requirement。

本节不开始 Contract Design，也不定义 Test Case、Grader、Metric 或任何后续评价对象。

## 14. Final Requirement Set

只有 Finalization Status 为 `FINALIZATION_READY` 时，才能产生 authoritative Final Requirement Set。Final Requirement Set 只使用已经冻结的 Requirement Schema，不增加字段：

| 字段 | 必填 | 规则 |
|---|---:|---|
| `requirement_id` | 是 | 当前 Benchmark 内稳定的 ID，例如 `R001` |
| `statement` | 是 | 清楚表达一项评估责任 |
| `source` | 是 | `skill`、`user`、`project`、`interface` 或 `other` |
| `source_ref` | 否 | 存在稳定位置时记录简短、可追溯的来源位置 |
| `evaluation_type` | 是 | `outcome` 或 `workflow` |

原文摘录、status、notes、不确定项、冲突细节和 normalization history 只保留在 Candidate Ledger、Extraction Issue Ledger、Normalized Candidate Set、Candidate Disposition Matrix 或 Traceability Review 中，不得加入冻结的 Requirement 对象。

最终 Requirement 必须同时满足：

- 表达规范性责任，而不只是当前 Implementation Fact；
- 具有合法来源并能够回溯；
- 属于当前 Eval 范围；
- 不是未解决冲突或未解决不确定项；
- 不只是背景、示例或细碎实现步骤；
- 其粒度保留了具有独立意义的可观察失败；
- 分类为 `outcome` 或 `workflow`；
- 后续能够进入 Contract Design，且没有嵌入 Grader assertion。

## 15. Decision Checklist

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

只有 Skill Summary、Requirement Candidate Ledger、Normalized Candidate Set、Candidate Disposition Matrix、完整的 Pass 4 Traceability Review、Finalization Mapping 和 Final Requirement Set 全部存在，Finalization Status 为 `FINALIZATION_READY`，并且 Checklist 没有未解释的失败时，Requirement Extraction 才完成。
