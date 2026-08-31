# Skill Eval CLI 使用说明 v0.1

## 范围

v0.1 CLI 是现有 schema、validation、digest、Runtime 和 evaluation API 之上的轻量 JSON 入口，只支持显式可执行的 `BenchmarkDefinitionV03` input。它不是 Subject executor、grader platform、registry 或 reporting application。

本文说明仓库本地安装方式与受支持的 v0.1 CLI 契约。

## 开发环境安装

在 Windows 仓库根目录执行：

```powershell
uv sync --frozen --extra dev
```

该命令会把 `skill-eval` console entry point 安装到 `.venv\Scripts`。

## 命令

验证可执行 v0.3 Definition 的结构与跨对象 graph：

```powershell
.venv\Scripts\skill-eval.exe validate assets\examples\minimal\definition.json
```

计算规范 v1 digest：

```powershell
.venv\Scripts\skill-eval.exe digest assets\examples\minimal\definition.json
```

运行确定性 evaluation pipeline，并写入完整 JSON bundle：

```powershell
.venv\Scripts\skill-eval.exe evaluate `
  --definition assets\examples\minimal\definition.json `
  --run-input assets\examples\minimal\run-input.json `
  --output evaluation.json
```

成功时向 stdout 写入精简 JSON 摘要，并把完整 result bundle 写到指定 output path。失败时向 stderr 写入结构化 JSON object，并返回非零 exit code。

## Evaluation input 契约

根 `input_version` 必须是 `skill-eval-evaluation-input/v0.1`。Input 只包含调用方控制的 identity、固定 timestamps 与 IDs、execution plan、已完成 Episode facts、Artifacts、合格 Evidence、GraderResults 和 Runtime diagnostics。

`definition_ref` 必须显式绑定：

- 与 Definition 相同的 benchmark ID 和 benchmark version；
- `skill-eval-frozen-definition-closure-v1`；
- `skill-eval digest` 打印的精确 digest；
- 可选 snapshot reference。

`result_ids` 为 Framework 将生成的 MetricResults、GateResults 与 Scorecard 提供稳定 IDs；其中 Metric 和 Gate keys 必须与 Definition 完全一致。

Input schema 禁止额外字段，尤其不接受调用方提供的 `metric_results`、`gate_results`、`overall_score_outcome` 或 `acceptance_evaluation`。

## Evaluation output 契约

Output root 是 `skill-eval-evaluation-output/v0.1`，包含：

- Definition identity 与 closure profile；
- 最终确认有效的 Run 和 completed Episodes；
- 上游 Artifacts、Evidence、GraderResults 与 diagnostics；
- Framework 生成的 MetricResults 与 GateResults；
- Framework 生成的 OverallScoreOutcome 与 AcceptanceEvaluation；
- 最终 Scorecard，以及完整 actual/missing inventory。

进入权威 output 的全部 IDs 与 timestamps 都来自 input。CLI 不调用 `uuid4`、`datetime.now` 或随机数生成器。使用相同文件重复评估会产生字节完全相同的 output JSON。

## 真实 Skill 示例

`real-skill` fixture 表示一个小型 Structured Task Summary Skill。Skill instructions 要求 JSON object 只包含 `summary`、`priority` 和 `next_action`。Subject execution 由预生成的 `subject-output.json` fixture 表示，并与 Framework evaluation 分离。

```powershell
.venv\Scripts\skill-eval.exe evaluate `
  --definition tests\fixtures\e2e\real-skill\definition.json `
  --run-input tests\fixtures\e2e\real-skill\run-input.json `
  --output real-skill-evaluation.json
```

合格 Evidence 支持 `satisfied` GraderResult。确定性 Metric 因此等于 `1`；Gate 检查该值是否小于 `1`，所以保持 `OPEN`；Overall 为 `1.00`；Acceptance 为 `ACCEPTABLE`；Scorecard 为 `finalized_evaluation`，且没有 missing applications。

## 错误类别

结构化 stderr 区分：`io_error`、`input_schema_error`、`definition_schema_error`、带 Definition issue codes 的 `definition_validation_error`、带 digest/profile binding issue codes 的 `definition_identity_error`、带 Runtime issue codes 的 `runtime_graph_error`、`evaluation_error` 和 `finalization_error`。

## 可信边界限制

`AUDIT-001` 仍是可信内部运行环境中的 accepted risk。受支持的 CLI path 会执行缓解措施：调用方提供的 GraderResults 是最后一类外部语义产物；随后 CLI 在 Runtime 与 Scorecard finalization 前调用 Framework 的确定性 Metric、Gate、Overall 与 Acceptance authority。

CLI 不证明任意调用方构造的派生 Results 已经过语义重算；绕过受支持路径的调用方不在受支持的 trust boundary 内。

`AUDIT-006` 已关闭。无版本后缀的聚合 Public Schema API 现在选择当前可执行 v0.3 models；历史 v0.2 兼容使用显式 `*V02` names。CLI 继续显式选择 `BenchmarkDefinitionV03` 与 closure profile v1。详见 `docs/public-api-version-policy-v0.1.md`。
