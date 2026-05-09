---
title: Python 高性能编程技巧
tags: [python, performance, programming]
created: 2026-05-09
---

## 列表推导式 vs 循环

列表推导式比普通 for 循环更快，因为它在 C 层面执行而非 Python 解释器层面：

```python
# 慢
result = []
for x in range(1000):
    result.append(x * 2)

# 快
result = [x * 2 for x in range(1000)]
```

## 生成器与内存优化

处理大数据集时使用生成器可以显著减少内存占用。生成器是惰性求值的，只在需要时才计算下一个值。

```python
def read_large_file(path):
    with open(path) as f:
        for line in f:
            yield line.strip()
```

## 使用 dataclass 简化类定义

Python 3.7+ 的 dataclass 装饰器可以自动生成 __init__、__repr__ 等方法，减少样板代码：

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
    label: str = ""
```

## 异步编程基础

async/await 语法让并发编程更加直观。asyncio 是 Python 标准库的一部分，适合 IO 密集型任务：

```python
import asyncio

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```
