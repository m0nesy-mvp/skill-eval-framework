# 技术主题：《Benchmark Definition → Requirement → Contract Schema Design v0》

> [!IMPORTANT]
> **文档角色：历史初始 Schema 设计基线。** 本文的“本轮不设计”与实现阶段限制只描述当时的设计范围，不是当前仓库能力状态。当前可执行 root 是 `BenchmarkDefinitionV03`；当前版本、Runtime 与 CLI 边界见 `docs/public-api-version-policy-v0.1.md`、`references/runtime-evaluation.md` 和 `references/cli.md`。

## 1. 文档范围

本设计只处理以下三个 Concept Object：

```text
Benchmark Definition
        ↓
Requirement
        ↓
Contract
```

本轮不设计：

- Test Case
- Evidence Specification
- Grader Specification
- Metric Specification
- Gate Specification
- Run
- Episode
- Result
- Scorecard

本文是 Schema Design，不是 Pydantic 实现，也不规定 YAML / JSON 文件格式、目录结构、CLI 或 Runtime 行为。

权威上游依据是：

```text
《通用 Skill Eval Design Process v1.1（Scope-Frozen）》
+
《Agent Skill Benchmark Concept Model v0.1》
```

设计原则：

```text
最小
清晰
可确定性验证
能够自然扩展到后续 Definition 对象
不为尚未出现的需求预留字段
```

## 2. 仓库基线 Check

设计开始时的仓库状态：

| 路径 | 当前状态 |
|---|---|
| `docs/` | 存在，包含 Design Process v1.1 与 Concept Model v0.1 |
| `src/` | 不存在 |
| `tests/` | 不存在 |
| `pyproject.toml` | 不存在 |

仓库中没有发现旧 MVP0 Python package、旧 Model、旧 Schema、旧测试或旧序列化格式。

因此本设计：

- 从零定义当前最小 Schema；
- 不兼容不存在的旧字段；
- 不保留迁移别名；
- 不添加 legacy adapter；
- 不为旧序列化格式设计兼容层。

## 3. 总体结构

三个对象的最小包含关系是：

```text
Benchmark Definition
├── requirements: list[Requirement]
└── contracts: list[Contract]
```

Requirement 与 Contract 的权威引用关系只保存在：

```text
Contract.requirement_ids
```

不同时保存：

```text
Requirement.contract_ids
```

Requirement 到 Contracts 的关系通过反向查询得到：

```text
给定 Requirement R001
↓
查找 requirement_ids 包含 R001 的 Contracts
```

这样可以避免双向关系分别编辑后发生漂移。

## 4. 技术主题：Benchmark Definition Schema

### 4.1 对象职责

Benchmark Definition 是 Definition 层的顶层容器。

在本模块中，它只负责：

- 标识一个 Benchmark lineage；
- 标识当前 Definition 版本；
- 提供人类可理解的名称和可选说明；
- 表示当前 Definition 是可修改还是已冻结；
- 包含 Requirement 集合；
- 包含 Contract 集合。

后续 Test Case、Evidence、Grader、Metric 和 Gate 对象不在本轮提前占位。

### 4.2 最终推荐字段

| 字段 | 类型 | 必填 | 用途 |
|---|---|---:|---|
| `benchmark_id` | `string` | 是 | 标识同一个 Benchmark 的稳定 lineage，不随普通版本升级改变 |
| `name` | `string` | 是 | 面向人类的简短 Benchmark 名称 |
| `version` | `string` | 是 | 标识当前 Frozen Definition 版本，未来 Run 通过它精确引用定义版本 |
| `description` | `string` | 否 | 对 Benchmark 目的或范围作简短补充；不拆分更多描述字段 |
| `status` | `enum: draft | frozen` | 是 | 表示 Definition 是否仍可修改；不表示 VALID / INVALID |
| `requirements` | `list[Requirement]` | 是 | 本 Benchmark 中进入范围的 Requirement 集合 |
| `contracts` | `list[Contract]` | 是 | 本 Benchmark 中对 Requirement 的可验证表达集合 |

### 4.3 benchmark_id 语义

`benchmark_id` 标识的是同一个 Benchmark 的稳定身份，而不是某一次 Definition 快照。

例如：

```text
Benchmark B001 v0.1
Benchmark B001 v0.2
```

这两个 Definition：

- `benchmark_id` 相同；
- `version` 不同；
- 表示同一个 Benchmark lineage 的两个版本。

只有当评估目标或 Benchmark 身份本身发生根本变化，不再适合视为同一套 Benchmark 的演进时，才创建新的 `benchmark_id`。

`benchmark_id` 不要求全局互联网唯一，也不承担数据库主键设计。本地项目或 Benchmark registry 未来需要保证同一管理范围内不会冲突。

### 4.4 version 语义

`version` 标识一个具体 Benchmark Definition 版本。

核心规则：

1. `draft` 可以在冻结前继续修改。
2. 一旦 `status = frozen`，该 `benchmark_id + version` 对应的 Definition 不可原地修改。
3. Frozen Definition 需要修改时：

```text
保持 benchmark_id
↓
创建新的 version
↓
修改新版本
↓
重新验证并冻结
```

4. 未来 Run 必须精确引用：

```text
benchmark_id + version
```

而不是只引用 `benchmark_id`。

本设计不强制完整 Semantic Versioning。v0 只要求 `version` 是非空、稳定、可比较的字符串，例如：

```text
v0.1
v0.2
v1.0
```

### 4.5 status 语义

第一版只保留两个生命周期状态：

```text
draft
frozen
```

#### 字段或协议值：draft

表示 Definition 仍可修改。

`draft` 不等于“允许任意错误类型或残缺对象”。一个 draft Definition 仍应符合基本 Schema；它可以尚未通过完整 Eval Design Validation。

#### 字段或协议值：frozen

表示该版本已经完成必要验证并作为执行规则冻结。

未来 Run 只能引用 Frozen Definition。

#### 不加入 VALID / INVALID

```text
draft / frozen
= Benchmark 生命周期状态

VALID / INVALID
= Eval Design Validation Result
```

两者语义不同，不能放进同一个 Enum。

#### 不加入其他状态

v0 不加入：

- archived
- deprecated
- active
- inactive
- published
- retired

这些状态目前没有阻塞 Requirement → Contract Schema 的真实需求。

## 5. 技术主题：Requirement Schema

### 5.1 对象职责

Requirement 回答：

> 为什么要评这一项？

进入 Benchmark Definition 的 Requirement 天然属于当前 Benchmark 范围，因此不添加 `in_scope`。

Out-of-scope、候选但未采纳或仍不确定的内容可以保留在设计工作记录中，不进入当前 Definition 的 `requirements`。

### 5.2 最终推荐字段

| 字段 | 类型 | 必填 | 用途 |
|---|---|---:|---|
| `requirement_id` | `string` | 是 | Requirement 在当前 Benchmark lineage 内的稳定标识 |
| `statement` | `string` | 是 | Requirement 本身的自然语言陈述 |
| `source` | `enum: skill | user | project | interface | other` | 是 | Requirement 的来源类型 |
| `source_ref` | `string` | 否 | 指向来源位置的简短可追溯说明 |
| `evaluation_type` | `enum: outcome | workflow` | 是 | 区分结果要求与工作流要求，不建立两套 Requirement 类 |

### 5.3 requirement_id 规则

推荐形式：

```text
R001
R002
R003
```

规则：

- 在一个 Benchmark Definition 中唯一；
- 不要求跨所有 Benchmark 全局唯一；
- 由 Agent Designer 生成；
- 使用 `R` 加至少三位十进制数字的稳定格式；
- 同一 Benchmark 新版本中，如果 Requirement 的评估意图保持不变，应保持原 ID；
- 只修改措辞、修正错别字或澄清原意，不需要新建 ID；
- 如果 Requirement 的来源、责任或评估意图发生重大变化，继续使用旧 ID 会误导历史追溯，则创建新 ID；
- 被删除的 ID 不应在同一 Benchmark lineage 中复用于不同语义。

跨版本 ID 是否正确延续属于版本审查判断，不能只通过单个 Definition 的局部 Schema 完成验证。

### 5.4 statement 规则

使用一个字段：

```text
statement: string
```

不同时增加：

- name
- title
- description
- content

Requirement 应拆分到一条 `statement` 能清楚表达一个评估要求的粒度。

`statement` 必须是去除首尾空白后仍非空的字符串。

### 5.5 source 规则

`source` 直接使用冻结方法论中的最小 Enum：

```text
skill
user
project
interface
other
```

不创建 Source Object。

### 5.6 source_ref 规则

`source_ref` 是 Optional string，用于记录例如：

- `SKILL.md` 某章节；
- 某 reference 文件及章节；
- 用户明确要求；
- 项目规范位置；
- 接口文档位置。

不把它升级成独立 Source Object，也不在 v0 中设计 URI、文件定位器或行号结构。

当没有稳定位置可引用时允许省略。存在时必须是非空字符串。

### 5.7 evaluation_type 规则

最小 Enum：

```text
outcome
workflow
```

不建立：

- OutcomeRequirement
- WorkflowRequirement

如果一段自然语言同时包含 Outcome 与 Workflow 两个独立责任，Agent 应将其拆成两个 Requirement，而不是新增 `mixed` 或 `shared` 类型。

## 6. 技术主题：Contract Schema

### 6.1 对象职责

Contract 回答：

> Requirement 怎样转化成可观察、可验证的责任？

Contract 不是 Grader。它描述人类可理解的成功、失败和风险语义，不包含 operator、threshold、regex、Python assertion 或具体评分实现。

### 6.2 最终推荐字段

| 字段 | 类型 | 必填 | 用途 |
|---|---|---:|---|
| `contract_id` | `string` | 是 | Contract 在当前 Benchmark lineage 内的稳定标识 |
| `requirement_ids` | `list[string]` | 是 | 该 Contract 承接的一个或多个 Requirement ID；权威关系只保存在这一侧 |
| `statement` | `string` | 是 | 可观察、可验证责任的自然语言陈述 |
| `evaluation_type` | `enum: outcome | workflow` | 是 | 区分 Outcome Contract 与 Workflow Contract |
| `criticality` | `enum: normal | critical` | 是 | 区分普通失败与会改变覆盖、证据强度或 Gate 设计决策的关键失败 |
| `success_criteria` | `list[string]` | 是 | 人类可理解的成功语义；不包含 Grader 实现 |
| `failure_criteria` | `list[string]` | 是 | 人类可理解的明确失败语义；不包含 Grader 实现 |
| `failure_modes` | `list[string]` | 是 | 已识别的主要失败方式，作为后续 Risk-driven Case Design 输入 |

### 6.3 contract_id 规则

推荐形式：

```text
C001
C002
C003
```

规则与 Requirement ID 对称：

- 在一个 Benchmark Definition 中唯一；
- 不要求全局唯一；
- 由 Agent Designer 生成；
- 使用 `C` 加至少三位十进制数字的稳定格式；
- 同一责任在 Definition 新版本中只做澄清时保持 ID；
- 成功语义、失败语义或责任边界发生根本变化，继续使用旧 ID 会误导历史追溯时创建新 ID；
- 被删除的 ID 不应在同一 Benchmark lineage 中复用于不同语义。

### 6.4 requirement_ids 规则

`requirement_ids` 必须支持多个 ID，因为 Concept Model 已冻结：

```text
Requirement N ↔ N Contract
```

规则：

- 必填；
- 至少包含一个 Requirement ID；
- 同一个 ID 不能在列表中重复；
- 所有 ID 必须存在于当前 Benchmark Definition 的 `requirements`；
- 不允许引用另一个 Benchmark Definition 中的 Requirement；
- Requirement 不保存反向 `contract_ids`。

### 6.5 statement 规则

只使用：

```text
statement: string
```

不增加：

- title
- name
- description
- responsibility

`statement` 应表达一个可观察、可验证的责任。如果一句话包含无法独立判断的多个责任，应拆成多个 Contract。

Schema 只能验证该字符串非空，不能确定性证明它是否真的“足够可验证”。

### 6.6 evaluation_type 兼容规则

Contract 与它引用的全部 Requirement 必须具有相同 `evaluation_type`。

例如：

```text
Requirement.evaluation_type = workflow
Contract.evaluation_type = workflow
→ 合法
```

```text
Requirement.evaluation_type = workflow
Contract.evaluation_type = outcome
→ 非法
```

如果一个 Contract 想同时承接 Outcome Requirement 和 Workflow Requirement，应拆成两个 Contract。

这样可以：

- 保持只有 `outcome / workflow` 两个枚举值；
- 避免新增 mixed 类型；
- 保持 Workflow Compliance 与 Outcome Eval 共用同一对象体系；
- 让类型兼容能够确定性验证。

### 6.7 criticality 规则

第一版只使用：

```text
normal
critical
```

#### 字段或协议值：normal

失败会影响评分或某个能力维度，但不自动表示整个 Benchmark 不可接受。

#### 字段或协议值：critical

失败会改变后续设计决策，例如：

- 需要更强 Case Coverage；
- 需要更强 Evidence；
- 可能成为 Gate 候选；
- 需要更严格的失败定位。

`critical` 不自动等于 Gate。是否建立 Gate 由后续 Gate Specification Design 决定。

不采用 `low / medium / high / critical` 四档，因为当前方法论真正需要的最小决策边界是：

```text
是否需要按 Critical Contract 特别处理
```

更多等级目前不会带来新的确定性 Framework 行为。

### 6.8 success_criteria 规则

使用：

```text
list[string]
```

而不是单个 string。

原因：

- 一个 Contract 可能同时需要多个成功条件；
- 列表比把多个条件塞进一个长句更容易阅读和后续映射；
- Agent 可以自然生成；
- 后续 Grader Design 可以逐项理解，但本字段本身不指定评分实现。

规则：

- 必填；
- 至少一个条目；
- 每个条目去除首尾空白后非空；
- 不允许完全相同的重复条目。

### 6.9 failure_criteria 规则

同样使用：

```text
list[string]
```

它表达明确的失败语义，而不是简单假设“未满足 success 就一定等价于所有失败情况”。

规则与 `success_criteria` 相同：

- 必填；
- 至少一个条目；
- 每个条目非空；
- 不允许完全相同的重复条目。

它不能包含具体 Grader operator、threshold、regex 或代码断言。

### 6.10 failure_modes 规则

使用：

```text
list[string]
```

并在 v0 中设为 Mandatory。

原因：

1. Design Process v1.1 将 Failure Modes 作为 Contract Design 的实际输出。
2. Core v1 明确要求 Framework 支持并实际使用 Failure Modes。
3. 它是下一阶段 Risk-driven Case Design 的直接输入。
4. 如果完全省略，Contract 到 Case Strategy 的关键设计依据会丢失。

规则：

- 必填；
- 至少一个条目；
- 每个条目非空；
- 不允许完全相同的重复条目。

Failure Mode 仍然不是一等对象。字符串列表已经足够支撑第一个版本。

## 7. 最终推荐 Schema 总表

### 技术主题：7.1 Benchmark Definition

| 字段 | 类型 | 必填 | 用途 |
|---|---|---:|---|
| `benchmark_id` | `string` | 是 | 稳定 Benchmark lineage ID |
| `name` | `string` | 是 | 人类可读名称 |
| `version` | `string` | 是 | Frozen Definition 版本 |
| `description` | `string` | 否 | 简短目的或范围说明 |
| `status` | `draft | frozen` | 是 | 生命周期状态 |
| `requirements` | `list[Requirement]` | 是 | Requirement 集合 |
| `contracts` | `list[Contract]` | 是 | Contract 集合 |

### 技术主题：7.2 Requirement

| 字段 | 类型 | 必填 | 用途 |
|---|---|---:|---|
| `requirement_id` | `string` | 是 | Benchmark-local Requirement ID |
| `statement` | `string` | 是 | Requirement 陈述 |
| `source` | `skill | user | project | interface | other` | 是 | Requirement 来源 |
| `source_ref` | `string` | 否 | 来源位置或说明 |
| `evaluation_type` | `outcome | workflow` | 是 | Outcome / Workflow 分类 |

### 技术主题：7.3 Contract

| 字段 | 类型 | 必填 | 用途 |
|---|---|---:|---|
| `contract_id` | `string` | 是 | Benchmark-local Contract ID |
| `requirement_ids` | `list[string]` | 是 | 指向一个或多个 Requirement |
| `statement` | `string` | 是 | 可验证责任陈述 |
| `evaluation_type` | `outcome | workflow` | 是 | Outcome / Workflow 分类 |
| `criticality` | `normal | critical` | 是 | 普通或关键 Contract |
| `success_criteria` | `list[string]` | 是 | 人类可理解的成功条件 |
| `failure_criteria` | `list[string]` | 是 | 人类可理解的失败条件 |
| `failure_modes` | `list[string]` | 是 | 主要失败方式 |

## 8. 验证规则

验证分成三个层次：

```text
A. Field Validation
B. Cross-object / Definition Validation
C. Agent Design Judgment
```

只有 A 和 B 可以作为确定性规则。C 不能伪装成 Schema Validator。

### 8.1 A. Field 验证

Field Validation 负责单个对象和单个字段的类型、格式及基础局部约束。

#### 技术主题：Benchmark Definition

- `benchmark_id` 必须是非空字符串。
- `benchmark_id` 必须以字母开头，后续只使用字母、数字、点、下划线或连字符。
- `name` 去除首尾空白后必须非空。
- `version` 去除首尾空白后必须非空。
- `description` 存在时去除首尾空白后必须非空。
- `status` 只能是 `draft` 或 `frozen`。
- `requirements` 必须是 Requirement 列表且至少一个元素。
- `contracts` 必须是 Contract 列表且至少一个元素。

#### 字段或协议值：Requirement

- `requirement_id` 必须符合 `R` 加至少三位十进制数字的格式。
- `statement` 去除首尾空白后必须非空。
- `source` 必须属于 `skill / user / project / interface / other`。
- `source_ref` 存在时去除首尾空白后必须非空。
- `evaluation_type` 必须是 `outcome` 或 `workflow`。

#### 字段或协议值：Contract

- `contract_id` 必须符合 `C` 加至少三位十进制数字的格式。
- `requirement_ids` 至少包含一个 ID。
- `requirement_ids` 中不允许完全相同的重复 ID。
- `statement` 去除首尾空白后必须非空。
- `evaluation_type` 必须是 `outcome` 或 `workflow`。
- `criticality` 必须是 `normal` 或 `critical`。
- `success_criteria` 至少一个非空条目，且不允许完全相同的重复条目。
- `failure_criteria` 至少一个非空条目，且不允许完全相同的重复条目。
- `failure_modes` 至少一个非空条目，且不允许完全相同的重复条目。

Field Validation 可以确定完全相同的重复值，但不能可靠判断两个不同自然语言句子是否语义重复。

### 8.2 B. Cross-object / Definition 验证

这些规则需要看到完整 Benchmark Definition，不能只验证单个 Requirement 或 Contract。

#### ID 唯一性

- `requirement_id` 在当前 Benchmark Definition 中唯一。
- `contract_id` 在当前 Benchmark Definition 中唯一。
- Requirement ID 与 Contract ID 分别在各自命名空间验证；前缀已经区分对象类型。

#### 引用合法性

- 每个 `Contract.requirement_ids` 至少包含一个 ID。
- `Contract.requirement_ids` 中的每个 ID 都必须存在于当前 `requirements`。
- Contract 不得引用其他 Benchmark Definition 中的 Requirement。

#### evaluation_type 兼容性

- Contract 的 `evaluation_type` 必须与它引用的每一个 Requirement 相同。
- 一个 Contract 不能同时引用 Outcome Requirement 与 Workflow Requirement。

#### Requirement → Contract 覆盖

- Frozen Benchmark 中，每个 Requirement 必须至少被一个 Contract 的 `requirement_ids` 承接。
- 未被任何 Contract 承接的 Requirement 使当前 Definition 无法冻结。

#### Frozen Definition 规则

- `status = frozen` 前必须通过当前模块的全部 Cross-object Validation。
- Frozen Definition 不允许原地修改。
- 修改 Frozen Definition 必须保持或重新确定 `benchmark_id` 语义，并创建新的 `version`。
- `benchmark_id + version` 在同一 Benchmark 管理范围内必须唯一。

“是否发生原地修改”和“版本组合是否已存在”需要版本库或上层管理边界提供历史上下文，不是单个文件的局部类型检查。

### 技术主题：8.3 C. Agent Design Judgment

以下问题需要 Agent 或 Human 进行语义判断，不能由确定性 Schema Validator 保证：

- Requirement 是否从 Target Skill 中提取得完整；
- Requirement 是否真的属于合法来源；
- Requirement statement 是否表达得清楚；
- 一条 Requirement 是否应该拆成多条；
- Contract 是否真的足够可观察、可验证；
- Contract 是否正确承接了 Requirement 的实际意图；
- success criteria 是否具有足够质量；
- failure criteria 是否准确且没有遗漏关键失败；
- failure modes 是否覆盖了真实风险；
- `criticality` 的设计判断是否合理；
- 两个不同自然语言 statement 是否语义重复；
- 某次措辞变化是否已经构成必须更换 ID 的“重大语义变化”。

这些内容可以进入设计审查、Agent workflow 或未来人工复核，但不能包装成确定性 Pydantic 验证结果。

## 9. Schema Validation 与 Eval Design Validation

```text
Schema Validation
≠
完整 Eval Design Validation
```

### 9.1 Schema / Object Validation 负责

- 字段类型；
- 必填字段；
- Enum 合法性；
- ID 基本格式；
- string 非空；
- list 非空；
- list 精确重复值；
- 单对象基础局部约束。

### 9.2 Benchmark-level Eval Design Validator 负责

当前模块可以定义但本轮不实现的确定性跨对象规则：

- Requirement ID 唯一；
- Contract ID 唯一；
- `Contract.requirement_ids` 全部存在；
- Contract 至少引用一个 Requirement；
- Contract 与 Requirement 的 `evaluation_type` 兼容；
- Frozen Benchmark 中每个 Requirement 至少被一个 Contract 承接；
- Frozen Definition 满足当前模块最低可执行结构。

后续模块加入后，完整 Eval Design Validator 还将负责：

- Contract → Test Case 覆盖；
- Critical Contract Coverage；
- Evidence Producer；
- Grader / Evidence Compatibility；
- Metric 来源；
- Weight 合法性；
- Gate 引用合法性。

这些后续规则只用于说明边界，不在本轮设计其 Schema 或实现。

### 9.3 生命周期与 Validation Result 分离

`status = frozen` 表示生命周期状态。

Eval Design Validator 的：

```text
VALID
INVALID + errors
```

是一次验证结果，不作为 Benchmark Definition 的 `status` 值，也不在本轮增加 `validation_result` 字段。

## 10. 被考虑但没有加入 v0 的字段

### 10.1 Benchmark Definition 未加入字段

| 候选字段 | 不加入原因 |
|---|---|
| `created_at` | 当前没有基于时间的执行或审计需求；Git 已提供文档历史 |
| `updated_at` | Frozen Definition 不应原地更新；当前不需要重复存储时间信息 |
| `schema_version` | 当前尚未建立独立序列化协议；先由代码包/文档版本确定 Schema，避免双版本漂移 |
| `methodology_version` | 上游方法论文档属于项目治理信息，不需要复制进每个 Benchmark |
| `concept_model_version` | 同上；当前没有 Runtime 解析需求 |
| `validation_result` | VALID / INVALID 是 Validator 输出，不是 Definition 固有字段 |
| `active` | 与 `status` 重复且语义模糊 |
| `frozen_at` | 当前没有真实时间审计需求 |
| `requirements_by_id` | 与 `requirements` 重复，会形成双重权威表示 |
| `contracts_by_id` | 与 `contracts` 重复，会形成双重权威表示 |
| `test_cases` | 属于下一个 Schema 模块，本轮不占位 |
| `evidence` | 属于后续 Evidence Specification，不提前设计 |
| `graders` | 属于后续 Grader Specification，不提前设计 |
| `metrics` | 属于后续 Metric Specification，不提前设计 |
| `gates` | 属于后续 Gate Specification，不提前设计 |

### 10.2 Requirement 未加入字段

| 候选字段 | 不加入原因 |
|---|---|
| `name` | 与 `statement` 重复 |
| `title` | 与 `statement` 重复 |
| `description` | 与 `statement` 重复 |
| `content` | 与 `statement` 重复 |
| `claim` | v1.1 已统一为 Requirement，不保留 Claim |
| `in_scope` | 进入 Benchmark Definition 的 Requirement 天然 in-scope |
| `contract_ids` | 权威关系只保存在 `Contract.requirement_ids`，避免双向漂移 |
| `criticality` | Criticality 是 Contract 属性，不是 Requirement 属性 |
| `failure_modes` | Failure Modes 属于 Contract 设计 |
| `source_object` | `source + source_ref` 已满足 v0 追溯需要，不建独立对象 |

### 10.3 Contract 未加入字段

| 候选字段 | 不加入原因 |
|---|---|
| `name` | 与 `statement` 重复 |
| `title` | 与 `statement` 重复 |
| `description` | 与 `statement` 重复 |
| `responsibility` | 与 `statement` 重复 |
| `requirement_id` | 不能表达 Requirement N ↔ N Contract，使用 `requirement_ids` |
| `gate` | Critical 不等于 Gate；Gate Specification 属于后续模块 |
| `gate_candidate` | 只是设计判断，不需要固化成 v0 字段 |
| `operator` | 属于 Grader Specification |
| `threshold` | 属于 Grader Specification 或 Metric/Gate Specification |
| `regex` | 属于具体 Grader 实现 |
| `assertion` | 属于 Grader Specification |
| `case_ids` | Contract ↔ Case 关系属于后续 Test Case Schema，不提前双向保存 |
| `evidence_ids` | 属于后续 Evidence Specification 关系 |
| `grader_ids` | 属于后续 Grader Specification 关系 |

## 11. 最小 YAML 概念示例

下面只用 YAML 形式验证字段组合是否自然，不创建真实 YAML 文件，也不定义最终序列化协议。

```yaml
benchmark_id: B001
name: Validator Workflow Benchmark
version: v0.1
description: 验证 Skill 是否按要求执行 validator，并在通过后生成最终结果。
status: frozen

requirements:
  - requirement_id: R001
    statement: Skill 必须在生成最终结果前执行 validator。
    source: skill
    source_ref: SKILL.md - Validation workflow
    evaluation_type: workflow

contracts:
  - contract_id: C001
    requirement_ids:
      - R001
    statement: 在最终结果生成之前，Skill 必须完成一次规定的 validator 执行。
    evaluation_type: workflow
    criticality: critical
    success_criteria:
      - 执行记录能够证明 validator 在最终结果生成前完成。
      - validator 的执行结果被保留供后续 Evidence 与 Grader 使用。
    failure_criteria:
      - Skill 在未执行 validator 的情况下生成最终结果。
      - Skill 在生成最终结果后才执行 validator。
    failure_modes:
      - 完全跳过 validator。
      - validator 执行顺序晚于最终结果生成。
      - 声称执行 validator，但没有可追溯的执行记录。
```

这个示例只验证：

- Benchmark 顶层包含 Requirement 和 Contract；
- Workflow Requirement 不需要第二套对象；
- Contract 可以通过 `requirement_ids` 引用 Requirement；
- 成功、失败和 Failure Modes 使用自然语言表达；
- 具体 Trace、Evidence 和 Grader 留给后续模块。

## 12. Workflow Requirement → Contract 示例

原始要求：

> Skill 必须在生成最终结果前执行 validator。

### 技术主题：12.1 Requirement

```text
requirement_id: R001
statement: Skill 必须在生成最终结果前执行 validator。
source: skill
source_ref: SKILL.md - Validation workflow
evaluation_type: workflow
```

它回答：

> 为什么要评 validator 执行顺序？

因为这是 Skill 自己声明的 Workflow Requirement。

### 技术主题：12.2 Contract

```text
contract_id: C001
requirement_ids: [R001]
statement: 在最终结果生成之前，Skill 必须完成一次规定的 validator 执行。
evaluation_type: workflow
criticality: critical
success_criteria:
  - 有执行事实表明 validator 在最终结果之前完成。
failure_criteria:
  - 未执行 validator 就生成最终结果。
  - 最终结果生成后才执行 validator。
failure_modes:
  - 跳过 validator。
  - validator 顺序错误。
  - 缺少可追溯执行记录。
```

它回答：

> 这条 Workflow Requirement 具体如何转化成可观察、可验证的责任？

不需要建立 `WorkflowRequirement` 或 `WorkflowContract` 类。两者都使用相同 Requirement / Contract Schema，并通过：

```text
evaluation_type: workflow
```

进行分类。

本轮不继续设计：

- 如何产生 validator Tool Trace；
- 哪个 Evidence Specification 消费 Trace；
- 哪个 Grader 判断顺序；
- 是否建立 Gate。

这些属于后续模块。

## 13. 待决问题

当前没有阻塞下一轮 Pydantic Implementation 的 Concept 或字段问题。

以下事项已在本设计中直接决定，不继续留作 Open Question：

- Benchmark 版本通过 `benchmark_id + version` 精确标识；
- 生命周期只使用 `draft / frozen`；
- Requirement 来源直接使用五值 Enum；
- Requirement 和 Contract 只使用 `outcome / workflow`；
- 混合责任通过拆分对象处理；
- Criticality 只使用 `normal / critical`；
- 成功、失败和 Failure Modes 使用 `list[string]`；
- `failure_modes` 在 v0 中必填；
- Requirement ↔ Contract 的权威关系只保存在 `Contract.requirement_ids`；
- Frozen Benchmark 中每个 Requirement 必须至少被一个 Contract 承接；
- 不加入 `schema_version`、时间戳或旧模型兼容字段。

下一阶段实现时仍需做少量代码层选择，例如具体 Python 类型名、错误消息文本和 Optional 字段的序列化表现。这些不改变本 Schema Design，也不构成 Concept 阻塞。

## 14. 本模块结论

第一个 Schema 模块冻结为：

```text
Benchmark Definition
├── benchmark_id
├── name
├── version
├── description（Optional）
├── status
├── requirements
└── contracts

Requirement
├── requirement_id
├── statement
├── source
├── source_ref（Optional）
└── evaluation_type

Contract
├── contract_id
├── requirement_ids
├── statement
├── evaluation_type
├── criticality
├── success_criteria
├── failure_criteria
└── failure_modes
```

该设计只确定最小字段、引用关系和验证边界，不包含 Pydantic 代码，不进入 Test Case 及后续 Schema。
