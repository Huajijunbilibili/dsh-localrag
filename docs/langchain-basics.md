# 示例文档 1：LangChain 基础概念

LangChain 是一个用于构建大语言模型（LLM）应用的框架。核心组件包括模型（Model）、提示词（Prompt）、输出解析（Parser）、记忆（Memory）和工具（Tool）。

## 1. 模型调用

通过统一的接口调用不同厂商的模型。以 DeepSeek 为例：

```python
from langchain_deepseek import ChatDeepSeek

llm = ChatDeepSeek(model="deepseek-chat")
response = llm.invoke("你好")
print(response.content)
```

## 2. 链（Chain）

链是把多个步骤串联起来的抽象。LangChain 0.3 之后官方推荐用 LangGraph 表达复杂流程，简单场景可以用 `prompt | llm | parser` 的管道写法。

## 3. 工具（Tool）

工具让模型获得外部能力。用 `@tool` 装饰器定义函数即可注册为工具，agent 会在需要时自动调用。

## 4. 记忆（Memory）

记忆让对话保持上下文。常见方案包括对话缓冲（buffer）、会话历史存储和向量记忆。

## 5. 关键要点

- 调用模型只需 base_url、model_name、api_key 三要素
- LCEL 管道适合简单场景，复杂状态流转用 LangGraph
- 工具是 agent 能力的来源，检索（RAG）是最常用的工具之一
