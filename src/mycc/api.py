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
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", sans-serif; display:flex; height:100vh; overflow:hidden; background:#f5f5f7; }

/* ---- sidebar ---- */
.sidebar {
  width:280px; min-width:280px; background:#1a1a2e; color:#ccd0e0;
  display:flex; flex-direction:column; overflow:hidden;
  box-shadow: 2px 0 12px rgba(0,0,0,.06);
}
.sidebar-header {
  padding:24px 20px 16px; border-bottom:1px solid rgba(255,255,255,.08);
}
.sidebar-header h1 { font-size:17px; color:#fff; font-weight:600; letter-spacing:.3px; }
.sidebar-header p { font-size:12px; color:#7c8099; margin-top:6px; }
.note-list { flex:1; overflow-y:auto; padding:12px 0; }
.note-folder {
  font-size:11px; color:#5a5d7a; padding:14px 20px 6px;
  text-transform:uppercase; letter-spacing:.6px; font-weight:600;
}
.note-item {
  display:flex; align-items:center; gap:8px; padding:11px 20px; cursor:pointer;
  font-size:13.5px; color:#9da0b8; text-decoration:none; border-left:3px solid transparent;
  transition:all .18s; position:relative;
}
.note-item:hover { background:#22223a; color:#d5d8ee; border-left-color:#56577a; }
.note-item.active {
  background:#22223a; color:#fff; border-left-color:#7c8cf8;
  font-weight:500;
}
.note-folder:first-child { padding-top:2px; }

/* ---- main area ---- */
.main { flex:1; display:flex; flex-direction:column; overflow:hidden; background:#fff; }
.topbar {
  padding:14px 40px; background:#fff; border-bottom:1px solid #eee;
  display:flex; align-items:center; gap:14px;
  box-shadow:0 1px 3px rgba(0,0,0,.02);
}
.topbar input {
  flex:1; max-width:480px; padding:9px 16px; border:1px solid #ddd; border-radius:8px;
  font-size:14px; outline:none; background:#f9f9fb; transition:all .2s;
}
.topbar input:focus { border-color:#7c8cf8; background:#fff; box-shadow:0 0 0 3px rgba(124,140,248,.1); }
.topbar button {
  padding:9px 20px; background:#1a1a2e; color:#fff; border:none; border-radius:8px;
  font-size:13px; cursor:pointer; white-space:nowrap; font-weight:500; transition:background .15s;
}
.topbar button:hover { background:#2e2e4a; }
.topbar .links { font-size:13px; color:#888; white-space:nowrap; margin-left:auto; }
.topbar .links a { color:#7c8cf8; text-decoration:none; margin-left:8px; font-weight:500; }

/* ---- content ---- */
.content { flex:1; overflow-y:auto; padding:40px 60px; }
.content > * { max-width:780px; margin-left:auto; margin-right:auto; }
.content :is(h1,h2,h3,h4) { margin:28px auto 14px; }
.content h1 { font-size:26px; font-weight:700; color:#1a1a2e; }
.content h2 { font-size:19px; font-weight:600; color:#1a1a2e; padding-bottom:8px; border-bottom:2px solid #eee; margin-top:40px; }
.content h3 { font-size:16px; font-weight:600; color:#333; }
.content p { margin:10px auto; line-height:1.85; font-size:15.5px; color:#3a3a3a; }
.content ul, .content ol { margin:10px auto; padding-left:28px; }
.content li { margin:5px 0; line-height:1.75; font-size:14.5px; color:#444; }
.content code { background:#f0f0f5; color:#d14; padding:2px 6px; border-radius:4px; font-size:13px; }
.content pre { background:#1a1a2e; color:#ccd0e0; padding:20px 24px; border-radius:10px; overflow-x:auto; margin:16px auto; }
.content pre code { background:none; padding:0; color:inherit; font-size:13.5px; }
.content blockquote { border-left:3px solid #7c8cf8; margin:16px auto; padding:6px 20px; color:#666; background:#f8f7ff; border-radius:0 6px 6px 0; }
.content strong { color:#1a1a2e; font-weight:600; }
.content table { border-collapse:collapse; margin:16px auto; font-size:13.5px; width:100%; }
.content th, .content td { border:1px solid #e5e5e5; padding:8px 14px; text-align:left; }
.content th { background:#f7f7fa; font-weight:600; color:#1a1a2e; }
.content img { max-width:100%; border-radius:6px; margin:12px auto; }
.empty { display:flex; align-items:center; justify-content:center; height:100%; color:#bbb; font-size:15px; }
.search-results { max-width:780px; margin:0 auto; }
.search-results h3 { font-size:14px; color:#888; margin-bottom:20px; }
.result-item {
  background:#fff; border:1px solid #eee; border-radius:10px; padding:18px 22px;
  margin-bottom:14px; cursor:pointer; transition:all .18s;
}
.result-item:hover { border-color:#7c8cf8; box-shadow:0 4px 16px rgba(0,0,0,.05); transform:translateY(-1px); }
.result-item .r-title { font-size:14.5px; font-weight:600; color:#1a1a2e; margin-bottom:4px; }
.result-item .r-meta { font-size:12px; color:#aaa; margin-bottom:8px; }
.result-item .r-preview { font-size:13.5px; color:#666; line-height:1.6; }
.loading { display:flex; align-items:center; justify-content:center; height:100%; color:#bbb; }

/* ---- meta header ---- */
.meta-header {
  background: linear-gradient(135deg, #f8f7ff 0%, #f0f4ff 100%);
  border: 1px solid #e8e4f8; border-radius: 12px;
  padding: 28px 32px; margin-bottom: 0;
}
.meta-title { font-size: 24px; font-weight: 700; color: #1a1a2e; margin: 0 0 14px 0; max-width: none; }
.meta-info { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; }
.meta-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.meta-tag {
  display: inline-block; background: #e8e0f8; color: #5b3e9e; font-size: 12px;
  padding: 3px 10px; border-radius: 14px; font-weight: 500;
}
.meta-extra { display: flex; gap: 16px; font-size: 13px; color: #888; }
.meta-extra a { color: #7c8cf8; text-decoration: none; font-weight: 500; }
.meta-extra a:hover { text-decoration: underline; }
.meta-divider { max-width: 780px; margin: 0 auto 32px; border-bottom: 2px solid #eee; }
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
  const groups = {};
  for (const n of noteList) {
    const dir = n.path.includes('/') ? n.path.split('/').slice(0,-1).join('/') : '';
    if (!groups[dir]) groups[dir] = [];
    groups[dir].push(n);
  }
  let html = '';
  for (const [dir, items] of Object.entries(groups)) {
    if (dir) html += '<div class="note-folder">📁 ' + dir + '</div>';
    for (const n of items) {
      html += '<a class="note-item" href="#" data-path="' + n.path + '" onclick="loadNote(event,\\''+n.path+'\\')"><span style="font-size:14px">📄</span> ' + (n.title || n.name) + '</a>';
    }
  }
  container.innerHTML = html;
}

function parseFrontmatter(md) {
  const m = md.match(/^---[ \t]*\n([\\s\\S]*?)\n---[ \t]*\n?([\\s\\S]*)$/);
  if (!m) return { meta:{}, body:md };
  const yaml = m[1];
  const body = m[2];
  const meta = {};
  for (const line of yaml.split('\n')) {
    const idx = line.indexOf(':');
    if (idx > 0) {
      let key = line.substring(0, idx).trim();
      let val = line.substring(idx+1).trim();
      if (val.startsWith('[') && val.endsWith(']')) {
        meta[key] = val.slice(1,-1).split(',').map(s=>s.trim().replace(/^['\"]|['\"]$/g,''));
      } else {
        meta[key] = val.replace(/^['\"]|['\"]$/g,'');
      }
    }
  }
  return { meta, body };
}

function renderMetaHeader(meta) {
  let h = '<div class="meta-header">';
  if (meta.title) h += '<h1 class="meta-title">' + meta.title + '</h1>';
  h += '<div class="meta-info">';
  if (meta.tags && meta.tags.length) {
    h += '<div class="meta-tags">';
    for (const t of meta.tags) {
      h += '<span class="meta-tag">#' + t + '</span>';
    }
    h += '</div>';
  }
  h += '<div class="meta-extra">';
  if (meta.created) h += '<span>📅 ' + meta.created + '</span>';
  if (meta.source) h += '<span>🔗 <a href="' + meta.source + '" target="_blank">来源</a></span>';
  h += '</div>';
  h += '</div>';
  h += '</div>';
  return h;
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
      const { meta, body } = parseFrontmatter(data.content);
      document.getElementById('content-area').innerHTML = renderMetaHeader(meta) + '<div class="meta-divider"></div>' + marked.parse(body);
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
      const { meta, body } = parseFrontmatter(data.content);
      document.getElementById('content-area').innerHTML = renderMetaHeader(meta) + '<div class="meta-divider"></div>' + marked.parse(body);
      document.getElementById('search-input').value = '';
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
        import frontmatter as fm
        files = get_markdown_files()
        result = []
        for f in files:
            post = fm.load(str(f))
            title = post.get("title", f.stem)
            result.append({
                "path": str(f.relative_to(NOTES_DIR)).replace("\\", "/"),
                "name": f.stem,
                "title": title,
            })
        return {"notes": result}

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
