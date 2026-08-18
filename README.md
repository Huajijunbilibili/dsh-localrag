# localrag-mcp — 本地文档 RAG 检索插件（DeepSeek Harness）

一个给 DeepSeek Harness 的 **agent 提供本地知识检索能力**的 MCP 工具插件：
agent 在对话中可以直接调用 `mcp__localrag__search` 等工具，对本地文档做**语义检索并带来源引用**的回答。

> 生态贡献：这是 DeepSeek Harness 官方贡献指南中"创建插件并分享"的实践项目，发布到 GitHub 后打上 `dsh-plugin` 话题即可被社区发现。

## 架构

```
DeepSeek Harness (dsh web)
   │  --patch localrag.cordis.yml
   ▼
@deepseek-ai/dsh-mcp-client  (官方通用 MCP 客户端)
   │  启动 stdio 子进程
   ▼
server.py  (Python, FastMCP)
   ├── index_documents(path)   # 扫描目录，分块 + 向量化，写入 Chroma
   ├── search(query, k)        # 语义检索，返回文本 + 来源路径 + 分数
   └── list_documents()        # 列出知识库中的文档
   │
   ├── 向量模型：fastembed / BAAI/bge-small-zh-v1.5（本地 ONNX，无需 API key）
   └── 向量库：Chroma（持久化到 ./data/chroma）
```

## 快速开始

```bash
# 1. 安装依赖（Python 3.10+）
cd localrag-mcp
pip install -r requirements.txt

# 2. 独立冒烟测试（不依赖 Harness）
python test-client.py
# 预期输出：tools: [...]; index: indexed 2 files, N chunks; search: 命中结果

# 3. 接入 DeepSeek Harness（在 harness 仓库根目录）
pnpm dsh web --patch D:\programing\python\LangChain\models\localrag-mcp\localrag.cordis.yml
# 首次会下载 bge-small-zh 模型（约 95MB，仅一次）

# 4. 在对话里使用
#    "先索引 D:\...\docs，然后检索：LangGraph 多 agent 是怎么协作的？"
#    agent 会依次调用 index_documents → search，并基于检索结果回答
```

## ✅ 验证结果（真实运行）

独立测试（`python test-client.py`）：

```
tools: ['index_documents', 'search', 'list_documents']
index: indexed 2 files, 4 chunks into 'documents'
search: 命中 langgraph-multiagent.md（top score 0.537，带 source 路径）
```

Harness 集成（`pnpm dsh web --patch localrag.cordis.yml`）实测：agent 按提示依次调用
`index_documents` → `search`，最终回答**带来源与得分引用**：

> 主要来源：langgraph-multiagent.md（chunk 0、1，检索得分 0.4851 / 0.2863）
> 补充背景：langchain-basics.md（得分 0.1219）

## 工具清单（agent 视角）

| MCP 工具名 | 说明 |
|---|---|
| `mcp__localrag__index_documents` | 索引目录下的 .md/.txt（递归），分块 + 向量化入库 |
| `mcp__localrag__search` | 语义检索 top-k，返回文本、来源路径、相关性分数 |
| `mcp__localrag__list_documents` | 列出知识库全部来源文档 |

## 设计要点

- **检索带来源**：每个 chunk 记录 `source`（文件绝对路径），agent 回答可溯源——这是区别于普通聊天的关键能力
- **全本地运行**：embedding 用 ONNX 本地推理，不依赖外部 embedding API，无需任何密钥
- **分块策略**：512 字符滑动窗口 + 64 重叠，中文文档友好（v2 可升级为语义分块）
- **增量索引**：`upsert` 按文件去重，重复索引同一目录不会产生重复向量

## Roadmap（v2）

- [ ] PDF / Word 支持（pdfplumber + python-docx）
- [ ] 语义分块（基于段落/标题，而非固定窗口）
- [ ] 用 LangChain 封装成标准 RAG 流程（多路召回 + 重排）
- [ ] 与多 agent 深度研究系统整合（检索 worker 复用本插件）
- [ ] 评估：用 RAGAS 对检索质量打分

## 简历用法

> **为 DeepSeek Harness 生态开发 dsh-plugin：本地文档 RAG 检索 MCP 插件（Python + Chroma + fastembed）**
> - 实现 index/search/list 三个 MCP 工具，agent 对话中可直接调用，检索结果带来源引用
> - 全本地向量化（bge-small-zh，ONNX）与持久化存储，无需外部 API
> - 通过官方 `--patch` 机制挂载，并完成独立冒烟测试与 Harness 集成验证

## 相关链接

- DeepSeek Harness 官方贡献指南（插件分享路径）：https://github.com/deepseek-ai/deepseek-harness
- 社区插件踩坑总结：[Discussion #380](https://github.com/deepseek-ai/deepseek-harness/discussions/380)
- MCP 通用客户端：`@deepseek-ai/dsh-mcp-client`
