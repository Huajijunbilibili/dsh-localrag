# 示例文档 2：LangGraph 多 Agent 协作

LangGraph 是 LangChain 官方推荐的 agent 编排框架，把 agent 建模为带共享状态的状态机。

## 1. 核心概念

- State（状态）：多个节点共享的数据结构
- Node（节点）：一个处理步骤，可以是一个 agent、一个函数
- Edge（边）：节点之间的连接，条件边（conditional edge）决定下一步走向

## 2. 多 Agent 协作模式

最常见的模式是 Supervisor（主管）+ Worker（工作者）：

- 主管 agent 负责把任务拆解为子任务并分派
- 多个 worker agent 各司其职（检索、分析、写作）
- 质检 agent 检查结果，不合格则打回重做

## 3. 为什么用状态机而不是循环

状态机让每个步骤可观察、可恢复、可测试。LangGraph 提供 checkpoint 持久化，中断后可以从任意节点恢复，这是生产级 agent 的关键能力。

## 4. 关键要点

- 多 agent 系统本质是带共享状态的状态机，不是多个 LLM 轮流聊天
- supervisor 的本质是一个把 worker 当作工具列表的 agent
- 质检循环必须设置最大重试次数，防止无限打回
- 版本注意：新版 API 使用 `from langgraph.supervisor import create_supervisor`
