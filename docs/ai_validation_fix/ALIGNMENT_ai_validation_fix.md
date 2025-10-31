# 对齐文档：AI校验前端修复

## 项目上下文分析
- 技术栈：Django + Bootstrap 前端模板；后端提供 `/video/novels/<pk>/...` 路由。
- 相关模板：`web/templates/video/novel_detail.html`（内含 AI 智能校验模态框与日志查看器）。
- 组件：`components/task-components.html` 为统一任务组件，但当前页面未实例化该 JS 类。
- 后端端点：
  - 停止任务：`/video/novels/<pk>/stop-task/`（POST，JSON：`{"task_id": ...}`）
  - 获取日志：`/video/novels/<pk>/task-log/?task_id=...`（GET）
  - 状态轮询：`/video/novels/<pk>/validation-status/<task_id>/`（GET）

## 原始需求与边界确认
- 修复 AI 校验模态框关闭按钮（避免误调用其他模态框函数）。
- 统一前端停止任务与获取日志端点，保证与后端实现对齐。
- 将状态映射到统一的 `bg-*` 样式类，避免混用旧 `badge-*`。
- 渲染日志时兼容后端返回的对象结构（`message`、`timestamp`、`level`）。
边界：不改动后端实现逻辑；不重构统一任务组件；仅前端模板与 JS 修补。

## 需求理解
- 模态框标题“AI智能校验”对应 `novel_detail.html` 模板。
- 旧实现部分使用 `/api/...` 端点，需替换为 `/video/novels/<pk>/...`。
- 停止按钮在日志查看器内生成，需绑定 id 以支持禁用。

## 疑问澄清（基于代码与行业常识自解）
1. 是否需要统一使用 `components/task-components.html`？当前页面没有实例化该组件类且端点指向 `/api/tasks/...`，暂不启用，避免冲突。
2. 状态映射标准？采用后端 Celery 状态：`PENDING/STARTED/PROGRESS/SUCCESS/FAILURE` → 中文与 `bg-*` 类。
3. CSRF 获取方式？页面已有 `getCookie('csrftoken')`，沿用。

## 智能决策策略
- 以后端现有路由为准调整前端端点。
- 保持最小改动原则，仅修复与校验相关的 UI 和 JS。
- 停止按钮追加 id，以便在停止后禁用。

## 最终共识产出位置
- 参见 `docs/ai_validation_fix/CONSENSUS_ai_validation_fix.md`