---
title: Transformer 注意力机制
tags: [nlp, transformer, deep-learning]
created: 2026-05-09
---

## 自注意力机制

自注意力（Self-Attention）是 Transformer 架构的核心组件。它允许模型在处理序列时关注序列中不同位置的信息。

核心公式：$\text{Attention}(Q,K,V) = \text{softmax}(\frac{QK^T}{\sqrt{d_k}})V$

其中 Q、K、V 分别代表 Query、Key、Value 矩阵，$d_k$ 是 Key 向量的维度。除以 $\sqrt{d_k}$ 是为了防止点积过大导致 softmax 梯度消失。

## 多头注意力

多头注意力（Multi-Head Attention）通过并行运行多个注意力头，让模型能够关注不同表示子空间的信息：

$\text{MultiHead}(Q,K,V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$

每个头的计算：$\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$

## 位置编码

Transformer 本身不具有处理序列顺序的能力，因此需要位置编码来注入位置信息。原始论文使用正弦位置编码：

$PE_{(pos,2i)} = \sin(pos / 10000^{2i/d_{model}})$
$PE_{(pos,2i+1)} = \cos(pos / 10000^{2i/d_{model}})$
