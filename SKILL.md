---
name: skill-eval-framework
description: 设计 Skill 基准，并以确定性方式验证、计算 digest 和评估可执行 BenchmarkDefinitionV03 文件，生成可追溯的 Scorecard。
---

# Skill Eval Framework

## 目的

使用本 Skill，可以把已经设计完成的 Skill 基准转换为确定、可追溯的评估。Framework 负责验证冻结的 Benchmark Definition、计算内容 identity、接收已经完成的 Runtime 事实和 GraderResults、派生 Metric/Gate/Overall/Acceptance 结果，并生成 Scorecard。

仓库同时提供从 Skill requirements 走向 Contracts、Test Cases、Evidence、Graders、Metrics 和 Gates 的设计参考。

## 适用场景

需要完成以下工作时使用本 Skill：

- 为 Agent Skill 设计 benchmark；
- 验证可执行 Benchmark Definition；
- 计算稳定的 Definition digest；
- 从合格的上游产物运行确定性评估；
- 生成可追溯的 Scorecard；
- 审计 Definition、Runtime 与 Result 的一致性。

## 不适用场景

本 Skill 不是通用 Agent runtime、LLM grader 托管平台、浏览器自动化系统、通用 Subject executor、benchmark leaderboard 或科学元评估平台。Subject execution 与 semantic grading 位于确定性 CLI 边界之外。

## 核心工作流

```text
Target Skill
-> Requirement
-> Contract
-> Test Case
-> Evidence Specification
-> Grader Specification
-> Metric Specification
-> Gate Specification
-> BenchmarkDefinitionV03
-> validation
-> digest v1
-> Runtime
-> GraderResults
-> Metric
-> Gate
-> Overall / Acceptance
-> Scorecard
```

benchmark 尚未完成设计时，阅读 [references/design-workflow.md](references/design-workflow.md)。构造 evaluation input 前，阅读 [references/runtime-evaluation.md](references/runtime-evaluation.md)。

## 使用流程

1. 确认 Target Skill revision，并冻结其权威 requirements。
2. 使用 references 设计 benchmark objects；Definition 冻结前禁止虚构 Runtime results。
3. 编写 `BenchmarkDefinitionV03` JSON 文档。
4. 运行 `skill-eval validate`；出现任何 schema 或跨对象问题时停止。
5. 运行 `skill-eval digest`；把精确的 v1 digest 和 Definition identity 绑定到 Run input。
6. 在 Framework 外执行 Subject 和 graders。只向 Framework 提供 Runtime facts、合格 Evidence、GraderResults、确定性 IDs 和 timestamps。
7. 运行 `skill-eval evaluate`，检查输出 Scorecard、missing-result inventory、diagnostics、Metric/Gate results、Overall 与 Acceptance。
8. 一起保存冻结 Definition、input、output、command、exit code 和 revision。Definition 修订后必须生成新的 digest 和 Run。

## 确定性入口

现有 CLI 是唯一的确定性脚本权威。禁止把 Metric、Gate、Overall、Acceptance、Runtime 或 digest 逻辑复制到包装脚本中。

```powershell
skill-eval validate assets\examples\minimal\definition.json
skill-eval digest assets\examples\minimal\definition.json
skill-eval evaluate `
  --definition assets\examples\minimal\definition.json `
  --run-input assets\examples\minimal\run-input.json `
  --output example-evaluation.json
```

安装方式、input/output contracts、错误和已验证示例结果见 [references/cli.md](references/cli.md)。

## 版本边界

- `BenchmarkDefinitionV03` 是当前可执行 Definition。
- v0.3 使用 `skill-eval-frozen-definition-closure-v1`。
- `BenchmarkDefinitionV02` 只用于历史兼容。
- v0.2 使用 `skill-eval-frozen-definition-closure-v0`。
- CLI 只接受 v0.3；v0.2 的自由文本策略不会进入可执行路径。

直接使用 Python API 前，阅读 [references/executable-policy-v03.md](references/executable-policy-v03.md) 和 [docs/public-api-version-policy-v0.1.md](docs/public-api-version-policy-v0.1.md)。

## 已知限制

`AUDIT-001` 仍为 `ACCEPTED_RISK`。受支持的 CLI 只接受上游 Runtime products 和 GraderResults；Framework 自行派生 Metric、Gate、Overall 和 Acceptance 结果。直接使用 Python 的调用方可以绕过这条路径，向最终完整性检查提交结构合法但语义错误的派生 Results。该残余风险只是被记录，并未修复。

`AUDIT-001`～`AUDIT-006` 的当前状态与验证入口见 [docs/audit-status-v0.1.md](docs/audit-status-v0.1.md)。历史设计文档中的阶段状态不得覆盖该当前状态表。

禁止根据一个通过的 Case 声称整个 Skill 正确；也禁止把结构检查通过当作 Evidence 或 Grader judgment 在语义上正确的证明。
