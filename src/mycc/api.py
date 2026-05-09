"""FastAPI REST API for the knowledge base."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .config import NOTES_DIR
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


HOME_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>mycc — 个人知识库</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; display:flex; height:100vh; overflow:hidden; }
.sidebar {
  width:260px; min-width:260px; background:#1e1e2e; color:#cdd6f4;
  display:flex; flex-direction:column; overflow:hidden;
}
.sidebar-header {
  padding:20px 16px 12px; border-bottom:1px solid #313244;
}
.sidebar-header h1 { font-size:18px; color:#f5f5f5; }
.sidebar-header p { font-size:12px; color:#a6adc8; margin-top:4px; }
.note-list { flex:1; overflow-y:auto; padding:8px 0; }
.note-item {
  display:block; padding:10px 16px; cursor:pointer; font-size:13px;
  color:#a6adc8; text-decoration:none; border-left:3px solid transparent;
  transition:all .15s;
}
.note-item:hover { background:#313244; color:#cdd6f4; }
.note-item.active { background:#313244; color:#f5f5f5; border-left-color:#89b4fa; }
.note-folder { font-size:11px; color:#585b70; padding:8px 16px 4px; text-transform:uppercase; letter-spacing:.5px; }
.main { flex:1; display:flex; flex-direction:column; overflow:hidden; background:#fafafa; }
.topbar {
  padding:12px 24px; background:#fff; border-bottom:1px solid #e0e0e0;
  display:flex; align-items:center; gap:12px;
}
.topbar input {
  flex:1; padding:8px 14px; border:1px solid #d0d0d0; border-radius:6px;
  font-size:14px; outline:none;
}
.topbar input:focus { border-color:#89b4fa; box-shadow:0 0 0 2px rgba(137,180,250,.2); }
.topbar button {
  padding:8px 16px; background:#1e1e2e; color:#fff; border:none; border-radius:6px;
  font-size:13px; cursor:pointer; white-space:nowrap;
}
.topbar button:hover { background:#313244; }
.topbar .links { font-size:13px; color:#585b70; white-space:nowrap; }
.topbar .links a { color:#1e66f5; text-decoration:none; margin-left:8px; }
.content { flex:1; overflow-y:auto; padding:32px 48px; max-width:860px; }
.content :is(h1,h2,h3) { margin:24px 0 12px; }
.content h1 { font-size:24px; }
.content h2 { font-size:18px; padding-bottom:6px; border-bottom:1px solid #e0e0e0; }
.content h3 { font-size:15px; }
.content p { margin:8px 0; line-height:1.7; font-size:15px; color:#333; }
.content ul, .content ol { margin:8px 0; padding-left:24px; }
.content li { margin:4px 0; line-height:1.6; font-size:14px; color:#444; }
.content code { background:#e8e8e8; padding:1px 5px; border-radius:3px; font-size:13px; }
.content pre { background:#1e1e2e; color:#cdd6f4; padding:16px; border-radius:8px; overflow-x:auto; margin:12px 0; }
.content pre code { background:none; padding:0; color:inherit; }
.content blockquote { border-left:3px solid #89b4fa; margin:12px 0; padding:4px 16px; color:#666; background:#f0f4ff; }
.content strong { color:#222; }
.content table { border-collapse:collapse; margin:12px 0; font-size:13px; }
.content th, .content td { border:1px solid #d0d0d0; padding:6px 12px; text-align:left; }
.content th { background:#f0f0f0; font-weight:600; }
.empty { display:flex; align-items:center; justify-content:center; height:100%; color:#999; font-size:15px; }
.search-results h3 { font-size:14px; color:#666; margin-bottom:16px; }
.result-item {
  background:#fff; border:1px solid #e0e0e0; border-radius:8px; padding:16px;
  margin-bottom:12px; cursor:pointer; transition:all .15s;
}
.result-item:hover { border-color:#89b4fa; box-shadow:0 2px 8px rgba(0,0,0,.06); }
.result-item .r-title { font-size:14px; font-weight:600; color:#1e1e2e; margin-bottom:4px; }
.result-item .r-meta { font-size:12px; color:#999; margin-bottom:6px; }
.result-item .r-preview { font-size:13px; color:#555; line-height:1.5; }
.loading { display:flex; align-items:center; justify-content:center; height:100%; color:#999; }
</style>
</head>
<body>
<div class="sidebar">
  <div class="sidebar-header">
    <h1>📖 我的知识库</h1>
    <p id="note-count"></p>
  </div>
  <div class="note-list" id="note-list"></div>
</div>
<div class="main">
  <div class="topbar">
    <input type="text" id="search-input" placeholder="搜索笔记..." onkeydown="if(event.key==='Enter')doSearch()" />
    <button onclick="doSearch()">搜索</button>
    <span class="links"><a href="/docs">API 文档</a></span>
  </div>
  <div class="content" id="content-area">
    <div class="empty">👈 选择左侧笔记开始阅读，或在上方搜索</div>
  </div>
</div>
<script>
let notes = [];
let currentView = 'browse'; // browse | search

async function init() {
  try {
    const r = await fetch('/notes');
    const data = await r.json();
    notes = data.notes;
    document.getElementById('note-count').textContent = notes.length + ' 篇笔记';
    renderNoteList(notes);
  } catch(e) {
    document.getElementById('note-count').textContent = '加载失败';
  }
}

function renderNoteList(noteList) {
  const container = document.getElementById('note-list');
  // Group by folder
  const groups = {};
  for (const n of noteList) {
    const dir = n.path.includes('/') ? n.path.split('/').slice(0,-1).join('/') : '';
    if (!groups[dir]) groups[dir] = [];
    groups[dir].push(n);
  }
  let html = '';
  for (const [dir, items] of Object.entries(groups)) {
    if (dir) html += '<div class="note-folder">' + dir + '</div>';
    for (const n of items) {
      html += '<a class="note-item" href="#" data-path="' + n.path + '" onclick="loadNote(event,\\''+n.path+'\\')">' + n.name + '</a>';
    }
  }
  container.innerHTML = html;
}

function loadNote(e, path) {
  e.preventDefault();
  document.querySelectorAll('.note-item').forEach(el => el.classList.remove('active'));
  e.target.classList.add('active');
  currentView = 'browse';
  document.getElementById('search-input').value = '';
  showLoading();
  fetch('/notes/' + path)
    .then(r => r.json())
    .then(data => {
      document.getElementById('content-area').innerHTML = marked.parse(data.content);
    });
}

async function doSearch() {
  const q = document.getElementById('search-input').value.trim();
  if (!q) { init(); return; }
  currentView = 'search';
  document.querySelectorAll('.note-item').forEach(el => el.classList.remove('active'));
  showLoading();
  try {
    const r = await fetch('/search', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({query:q, top_k:10})
    });
    const data = await r.json();
    renderSearchResults(q, data.results);
  } catch(e) {
    document.getElementById('content-area').innerHTML = '<div class="empty">搜索出错</div>';
  }
}

function renderSearchResults(q, results) {
  if (!results || results.length === 0) {
    document.getElementById('content-area').innerHTML = '<div class="empty">未找到匹配结果</div>';
    return;
  }
  let html = '<div class="search-results"><h3>搜索 "' + q + '" — ' + results.length + ' 条结果</h3>';
  for (const r of results) {
    html += '<div class="result-item" onclick="openNote(\\''+r.file+'\\')">';
    html += '<div class="r-title">' + r.title + '  <span style="color:#89b4fa;font-size:12px">' + (r.score*100).toFixed(1) + '%</span></div>';
    html += '<div class="r-meta">' + r.file + '</div>';
    html += '<div class="r-preview">' + r.content.substring(0,150).replace(/\\n/g,' ') + '...</div>';
    html += '</div>';
  }
  html += '</div>';
  document.getElementById('content-area').innerHTML = html;
}

function openNote(path) {
  showLoading();
  fetch('/notes/' + path)
    .then(r => r.json())
    .then(data => {
      document.getElementById('content-area').innerHTML = marked.parse(data.content);
      document.getElementById('search-input').value = '';
      // Highlight sidebar
      document.querySelectorAll('.note-item').forEach(el => {
        el.classList.remove('active');
        if (el.dataset.path === path) el.classList.add('active');
      });
    });
}

function showLoading() {
  document.getElementById('content-area').innerHTML = '<div class="loading">加载中...</div>';
}

init();
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

    @app.get("/", include_in_schema=False)
    def home():
        return HTMLResponse(HOME_HTML)

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
