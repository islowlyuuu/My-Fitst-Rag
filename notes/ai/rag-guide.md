---
title: RAG 检索增强生成原理
tags: [nlp, rag, llm]
created: 2026-05-09
---

## RAG 基本流程

检索增强生成（Retrieval-Augmented Generation）将信息检索与文本生成相结合：

1. 将知识库文档分块并向量化存入向量数据库
2. 用户提问时，在向量数据库中检索最相关的文档块
3. 将检索结果作为上下文注入 LLM 的 prompt
4. LLM 基于检索到的知识生成回答

## 分块策略

合理的分块策略对 RAG 效果至关重要：

- 按语义段落分块：保留完整的语义单元
- 重叠分块：相邻块之间保留一定重叠，避免信息断裂
- 小 chunk 检索 + 大 chunk 返回：用小粒度检索提高召回，返回大粒度保留上下文

## Embedding 模型选择

中文场景推荐使用针对中文优化的模型：

- BGE 系列：BAAI/bge-large-zh-v1.5 效果最好
- M3E 系列：moka-ai/m3e-base 轻量且效果好
- text2vec 系列：shibing624/text2vec-base-chinese

向量维度通常在 512-1024 之间，维度越高表达能力越强但检索越慢。
