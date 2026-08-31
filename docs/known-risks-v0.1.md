# 已知风险 v0.1

## 1. 目的与范围

本文记录 `skill-eval-framework` 内部 v0.1 release 明确接受的风险。

这是 release risk register。它不修改 Frozen Definition、Evaluation、Runtime 或 Result 设计，也不声称已接受风险已经修复或关闭。

## 2. AUDIT-001 — 未独立重算派生语义结果

**状态：** `ACCEPTED_RISK`

**原始审计严重程度：** 原始严格审计模型下的 `P0`

**范围：** 内部可信执行环境

### 2.1 技术发现项

当前 final integrity 会验证结构与引用完整性，但不会独立重算调用方提供的 `MetricResult`、`GateResult`、`OverallScoreOutcome` 或 `AcceptanceEvaluation` 语义。

这保留了 Full Design-to-Code Audit 的发现项：直接使用 Python 的调用方可以构造结构合法但语义错误的派生 Result 对象；当前 final integrity 在没有 expected-vs-actual 语义验证的情况下仍可能接受这些对象。

### 2.2 风险接受决定

内部 v0.1 release 接受 `AUDIT-001`，因为受支持的内部执行工作流只通过确定性 evaluation services 派生全部语义 Results：

```text
GraderResults
-> deterministic Metric evaluator
-> deterministic Gate evaluator
-> Overall evaluator
-> Acceptance evaluator
-> finalization
```

直接向 finalization 提供业务代码构造的派生语义 Result 对象，不属于受支持的执行工作流。

### 2.3 残余风险

直接使用 Python 的调用方仍能构造结构合法但语义错误的派生 Result 对象。当前 final integrity 不会独立重算其语义，因此“可信环境”仍是通过工作流执行的约定，而不是 finalization 边界保证。

### 2.4 缓解措施

正式 CLI 与 orchestration path 必须（MUST）只传入由确定性 Metric、Gate、Overall 和 Acceptance evaluation services 生成的派生 Results。禁止（MUST NOT）把业务代码构造的派生语义 Results 当成 finalization 的受支持 input。

### 2.5 后续加固

在 finalization 边界增加确定性语义完整性重算或等价的 expected-vs-actual 验证。验证应复用确定性 evaluation authority，禁止引入第二套 Metric、Gate、Overall 或 Acceptance 语义实现。

### 2.6 未关闭声明

```text
AUDIT-001 != CLOSED
AUDIT-001 != FIXED
AUDIT-001 == ACCEPTED_RISK
```

风险接受决定只改变 release 处理方式，不会降低原始发现项在严格审计模型下的严重程度，不会改变技术事实，也不能作为已实现语义完整性验证的证据。
