# 共识文档：AI校验前端修复

## 明确的需求与验收标准
- 停止按钮具备 `id="validationStopBtn"`，停止后按钮被禁用。
- `stopValidationTask()` 使用 `/video/novels/<pk>/stop-task/`，传递 JSON `{ task_id }` 与 CSRF 头。
- `fetchValidationTaskLog()` 使用 `/video/novels/<pk>/task-log/?task_id=...`，正确渲染日志与进度。
- 状态徽章统一使用 `bg-*` 类并显示中文状态文本。

## 技术实现方案与约束
- 仅修改 `web/templates/video/novel_detail.html` 中相关 DOM 与 JS。
- 不重构统一任务组件类；后续可迁移但不在当前范围。
- 复用已有 `getCookie('csrftoken')` 以获取 CSRF。

## 集成方案
- 与后端 `views.get_task_log`、`views.stop_task` 对齐参数与返回结构。
- 日志级别 `info/warning/error` 映射到相应的样式类与图标（当前先以文本+颜色展示）。

## 任务边界与验收
- 边界：不修改后端逻辑、不变更其他页面。
- 验收：手动运行任务、查看日志、点击“停止”并验证禁用与状态更新。

## 不确定性解决确认
- 路由、返回结构、CSRF、状态映射均已在代码与文档中确认，无剩余阻塞性问题。