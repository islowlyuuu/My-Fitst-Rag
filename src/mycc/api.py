"""FastAPI REST API for the knowledge base."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import NOTES_DIR, TOP_K_DEFAULT
from .indexer import run_index, get_index_stats, get_markdown_files
from .models import SearchRequest
from .retriever import search

SWAGGER_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>mycc - API 文档</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({
  url: '/openapi.json',
  dom_id: '#swagger-ui',
  presets: [SwaggerUIBundle.presets.apis],
  layout: "BaseLayout",
  defaultModelsExpandDepth: -1,
  docExpansion: "list",
  filter: true,
  showCommonExtensions: true,
  language: 'zh-CN',
  translations: {
    zh_CN: {
      "Expand operations": "展开接口",
      "Collapse operations": "收起接口",
      "Try it out": "调试",
      "Cancel": "取消",
      "Execute": "发送请求",
      "Clear": "清除",
      "Responses": "响应",
      "Request body": "请求体",
      "Server response": "服务器响应",
      "Code": "状态码",
      "Details": "详情",
      "No parameters": "无参数",
      "Parameter": "参数",
      "Value": "值",
      "Description": "描述",
      "Authorize": "授权",
      "Close": "关闭",
      "Available authorizations": "可用授权",
      "Download": "下载",
      "Loading...": "加载中...",
      "Response body": "响应内容",
      "Response headers": "响应头",
      "Curl": "Curl命令",
      "Request URL": "请求地址",
      "Server": "服务器",
      "Schemes": "协议",
      "Nothing to preview": "无预览内容",
      "Example Value": "示例值",
      "Schema": "模型",
      "Model": "模型",
      "Models": "数据模型",
      "Select an option": "选择",
      "Search": "搜索",
    }
  }
})
</script>
</body>
</html>"""


def create_app() -> FastAPI:
    app = FastAPI(
        title="mycc — AI 个人知识库 API",
        description="""
## 功能

- **语义搜索**：基于向量相似度的智能检索
- **笔记管理**：浏览和查看知识库中的笔记
- **索引管理**：触发向量索引的增量/全量重建

## 当前支持的笔记格式

支持 Markdown + YAML Frontmatter 格式的笔记文件。
        """,
        version="0.1.0",
        docs_url=None,
    )

    @app.get("/docs", include_in_schema=False)
    def custom_swagger():
        return HTMLResponse(SWAGGER_HTML)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["系统"], summary="健康检查")
    def health():
        """检查服务是否正常运行"""
        return {"status": "ok"}

    @app.get("/stats", tags=["系统"], summary="索引统计")
    def stats():
        """获取当前知识库的索引统计信息"""
        return get_index_stats()

    @app.post("/search", tags=["检索"], summary="语义搜索")
    def search_endpoint(req: SearchRequest):
        """根据查询内容在知识库中检索最相关的笔记片段"""
        results = search(req.query, top_k=req.top_k, tag=req.tag)
        return {"results": results, "query": req.query}

    @app.get("/notes", tags=["笔记"], summary="列出所有笔记")
    def list_notes():
        """获取知识库中所有笔记的列表"""
        files = get_markdown_files()
        return {
            "notes": [
                {
                    "path": str(f.relative_to(NOTES_DIR)).replace("\\", "/"),
                    "name": f.stem,
                }
                for f in files
            ]
        }

    @app.get("/notes/{path:path}", tags=["笔记"], summary="查看笔记内容")
    def get_note(path: str):
        """根据文件路径获取单篇笔记的完整内容"""
        note_path = NOTES_DIR / path
        if not note_path.exists():
            raise HTTPException(status_code=404, detail="笔记不存在")
        return {
            "path": path,
            "content": note_path.read_text(encoding="utf-8"),
        }

    @app.post("/reindex", tags=["系统"], summary="重建索引")
    def reindex(force: bool = True):
        """强制全量重建向量索引"""
        num_files, num_chunks = run_index(force=force)
        return {"indexed_files": num_files, "indexed_chunks": num_chunks}

    return app
