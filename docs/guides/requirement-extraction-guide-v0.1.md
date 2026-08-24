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
5. **Traceability Review**：集合级双向来源覆盖审查；
6. **Final Requirement Set**：只包含已接受 Requirement，并使用冻结的 Requirement Schema。

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

Pass 3 必须为每一条 Pass 2 Candidate 给出一个明确 disposition：

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

| Disposition | 含义 |
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
11. 在 Candidate Disposition Matrix 中记录处置，并生成或更新 Normalized Candidate。

处理顺序是审查路径，不代表每一步都必须改变 Candidate。任何 SPLIT、MERGE、REMOVE 或 wording 修改都必须保留原 Candidate、来源证据和 extraction issue 的可追溯关系。

#### Pass 3 必需输出

Pass 3 必须产生：

1. **Normalized Candidate Set**：使用临时 `NR-` ID，记录通过 Normalize 的候选责任及其来源、类型、派生关系和 issue 关联。
2. **Candidate Disposition Matrix**：确保每条原始 `RC-` Candidate 都有 disposition、目标 Normalized Candidate 或无目标原因。
3. **Normalization Status**：只能是 `NORMALIZATION_READY` 或 `NORMALIZATION_BLOCKED`。

#### Pass 3 Completion Gate

进入 Pass 4 前确认：

- [ ] Pass 2 状态为 `COLLECTION_READY`
- [ ] 每个 `RC-` Candidate 都有 disposition
- [ ] 没有静默丢失 Candidate
- [ ] 所有 Normalized Candidate 都有 Normative Source 支持
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

Atomicity 不由动词数量、句子长度、标点或 bullet 数量决定。对于 Candidate 中可能包含的责任 A 和 B，检查：

1. A 是否可以满足而 B 不满足，或 B 可以满足而 A 不满足；
2. 这两种失败是否产生可区分、值得独立记录的评估结论。

两个条件都成立时使用 `SPLIT`。如果只是同一责任的自然组成动作，或拆开后不会增加诊断价值，不因文字结构机械拆分。

抽象地说，“必须执行规定的验证，并且最终结果必须满足该验证要求”可能包含两个可独立失败的责任：执行验证属于 workflow，最终结果满足要求属于 outcome。是否拆分仍取决于实际 Normative Source 是否分别支持这两个责任。

### 8.3 Merge Test

多个 Candidate 满足以下任一情形时，考虑 `MERGE`：

- 表达同一规范责任；
- 只是不同来源对同一责任的重复支持；
- 只是语义等价的改写；
- 在可观察评估意义上基本同真同假，独立评分不会增加有价值的失败结论。

判断核心是 diagnostic value，而不是措辞相似度。MERGE 不得隐藏不同 scope、不同 `evaluation_type`、独立失败模式、独立授权边界或具有单独意义的来源强调。

合并后必须保存所有适用的 `source_evidence`、`related_issue_ids` 和原 Candidate 关系。Normalized Candidate 的 `derived_from_candidate_ids` 必须包含全部被合并 Candidate；Candidate Disposition Matrix 对每条原 Candidate 分别记录 `MERGE` 和同一个目标 `NR-` ID。

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

此处不要求编写 Grader assertion、正则表达式、数值阈值或可执行 checker。如果连失败含义都无法描述，说明 statement 仍太模糊、粒度不合理，或 Normative Source 信息不足，应继续 Normalize 或标记 `NEEDS_CLARIFICATION`。

Contractability 不等于已经可自动测试，也不要求在 Pass 3 选择验证方法。

### 8.8 Multi-source Normalization

一个 Normalized Candidate 可以由多个 Normative Sources 支持。Normalize 时必须：

- 合并完全重复的 source evidence entry；
- 保留每个 `source_ref` 与自己的 `source_excerpt` 配对；
- 保留需要的 authority / delegation context；
- 不把多个来源压缩成无法追溯的单一字符串；
- 确认每项 evidence 支持 Normalized statement 的适用部分。

如果多个来源只是重复支持同一责任，应形成一个 Normalized Candidate，并通过 `derived_from_candidate_ids` 和完整 `source_evidence` 保留来源与 Candidate 历史。

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

- 相关 Candidate 使用 `CONFLICT` disposition；
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
| `source_evidence` | 成对保留引用与摘录的一个或多个 Normative Source evidence |
| `derived_from_candidate_ids` | 产生该记录的全部原始 `RC-` Candidate IDs |
| `related_issue_ids` | unresolved issue、已解决 issue 或 relevant mismatch 的关联 IDs |
| `disposition_summary` | 该结果由 `KEEP`、`KEEP_WITH_EDIT`、`SPLIT`、`MERGE` 或其他何种处置形成 |
| `normalization_rationale` | 来源支持、粒度、类型、wording 和 issue 处理理由 |
| `status` | `NORMALIZED`、`CONFLICT` 或 `NEEDS_CLARIFICATION` |

`NORMALIZED` 表示该 Candidate 已通过 Pass 3 的来源、粒度、类型、statement 和 contractability 检查，可以进入 Pass 4。`CONFLICT` 和 `NEEDS_CLARIFICATION` 保留问题状态，不得伪装成可直接进入 Final Requirement Set 的正常 Candidate。

Normalized Candidate Set 不是 Final Requirement Set，不修改 Frozen Requirement Schema，也不证明 source-level completeness。

### 11.2 Candidate Disposition Matrix

Candidate Disposition Matrix 是 Pass 3 的必需审计产物，用于证明每一条原始 Candidate 都有明确去向。至少记录：

| 字段 | 用途 |
|---|---|
| `candidate_id` | 原始 `RC-` ID |
| `disposition` | `KEEP`、`KEEP_WITH_EDIT`、`SPLIT`、`MERGE`、`REMOVE`、`DEMOTE_TO_NOTE`、`CONFLICT` 或 `NEEDS_CLARIFICATION` |
| `normalized_target_ids` | 零个、一个或多个目标 `NR-` IDs |
| `rationale` | 处置原因，包括来源、粒度、重复、类型或 issue 判断 |

Disposition 与目标关系必须清楚：

```text
一个 RC → SPLIT → 多个 NR
多个 RC → MERGE → 一个 NR
一个 RC → REMOVE / DEMOTE_TO_NOTE → 无 NR，并记录原因
一个 RC → KEEP / KEEP_WITH_EDIT → 一个 NR
```

Matrix 不得省略被删除、降级、冲突或待澄清的 Candidate。`derived_from_candidate_ids` 与 Matrix 应能相互核对，但这种 Candidate-level disposition 审计不是 Pass 4 的 source-level completeness Trace。

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

## 12. Final Requirement Set

Final Requirement Set 只使用已经冻结的 Requirement Schema，不增加字段：

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

只有 Skill Summary、Requirement Candidate Ledger、Normalized Candidate Set、Candidate Disposition Matrix、Traceability Review 和 Final Requirement Set 全部存在，并且 Checklist 没有未解释的失败时，Requirement Extraction 才完成。
