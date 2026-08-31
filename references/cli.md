# CLI 参考

## 仓库开发安装

```powershell
uv sync --frozen --extra dev
```

该命令把 `skill-eval` 安装到 `.venv\Scripts`。可以激活环境，也可以直接使用 executable path。

## 命令

```powershell
skill-eval validate assets\examples\minimal\definition.json
skill-eval digest assets\examples\minimal\definition.json
skill-eval evaluate `
  --definition assets\examples\minimal\definition.json `
  --run-input assets\examples\minimal\run-input.json `
  --output example-evaluation.json
```

`validate` 接受 v0.3 Definition，并执行 schema 与跨对象验证。`digest` 输出 closure-v1 SHA-256 identity。`evaluate` 验证 binding、检查 Runtime graph、派生全部下游结果，并写出完整 JSON bundle。

公开示例成功时会得到：有效且已完成的 Run、值为 `1` 的 available Metric、`OPEN` Gate、Overall `1.00`、Acceptance `ACCEPTABLE`，以及 `finalized_evaluation` Scorecard。

## Input/output 契约

- Input root：`skill-eval-evaluation-input/v0.1`。
- Output root：`skill-eval-evaluation-output/v0.1`。
- Input 只接受上游 Runtime products 和 GraderResults。
- 为保证确定性输出，Result IDs 与 timestamps 由调用方提供。
- 使用完全相同的文件重复评估，会生成字节完全相同的 JSON。
- 成功时向 stdout 写入精简摘要，并向 `--output` 写入完整 bundle。
- 失败时向 stderr 写入结构化 JSON，并返回非零 exit code。

错误类别包括 I/O、input schema、Definition schema/validation、Definition identity、Runtime graph、evaluation 与 finalization errors。

更完整的契约参考见 `docs/cli-usage-v0.1.md`。
