#!/usr/bin/env python3
"""
Полнофункциональная визуализация Git с просмотром изменений.
Улучшенный интерфейс: граф на всю ширину, компактная правая панель.
"""

import subprocess
import json
import sys
import os
import argparse
import webbrowser
import threading
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

PORT = 8888
CACHE_FILE = ".git_viz_cache.json"

# ----------------------------------------------------------------------
#  Git-команды
# ----------------------------------------------------------------------

def run_git(*args):
    try:
        result = subprocess.run(
            ['git'] + list(args),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception:
        try:
            result = subprocess.run(
                ['git'] + list(args),
                capture_output=True,
                text=True,
                errors='replace'
            )
            return result.stdout.strip()
        except:
            return ""

def get_all_commits(max_commits: int = 0, path_filter: str = "", since_commit: str = "") -> Dict[str, Dict]:
    cmd = ['rev-list', '--all']
    if since_commit:
        cmd = ['rev-list', since_commit]
    if path_filter:
        cmd.append('--')
        cmd.append(path_filter)
    hashes_raw = run_git(*cmd)
    if not hashes_raw:
        return {}
    hashes = hashes_raw.splitlines()
    if max_commits > 0 and len(hashes) > max_commits:
        hashes = hashes[:max_commits]
        print(f"Ограничение: загружено только {max_commits} коммитов")
    print(f"Найдено коммитов: {len(hashes)}")

    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except:
            pass

    head_hash = run_git('rev-parse', 'HEAD')
    cache_valid = (cache.get('head_hash') == head_hash and
                   cache.get('path_filter') == path_filter and
                   cache.get('since_commit') == since_commit)

    commits = {}
    missing_hashes = []
    for h in hashes:
        if cache_valid and h in cache.get('commits', {}):
            commits[h] = cache['commits'][h]
        else:
            missing_hashes.append(h)

    if missing_hashes:
        print(f"Загрузка деталей для {len(missing_hashes)} коммитов...")
        for h in missing_hashes:
            content = run_git('cat-file', '-p', h)
            if not content:
                continue
            parents = []
            message = ""
            author = ""
            author_name = ""
            date_timestamp = 0
            date_str = ""
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if line.startswith('parent '):
                    parents.append(line[7:])
                elif line.startswith('author '):
                    parts = line.split()
                    if len(parts) >= 5:
                        timestamp = parts[-2]
                        date_timestamp = int(timestamp)
                        dt = datetime.fromtimestamp(date_timestamp)
                        date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        author_full = line[7:].rsplit(' <', 1)[0]
                        author = author_full
                        author_name = author_full.split('<')[0].strip()
                elif line == '':
                    msg_lines = lines[i+1:]
                    if msg_lines:
                        message = '\n'.join(msg_lines).strip()[:100]
                    break
            commits[h] = {
                "parents": parents,
                "message": message,
                "author": author,
                "author_name": author_name or author.split('<')[0].strip(),
                "date_timestamp": date_timestamp,
                "date_str": date_str,
                "hash": h
            }
        cache_data = {
            "head_hash": head_hash,
            "path_filter": path_filter,
            "since_commit": since_commit,
            "commits": commits
        }
        if cache_valid:
            cache['commits'].update(commits)
            cache_data = cache
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"Кэш сохранён в {CACHE_FILE}")
    else:
        print("Использован кэш")

    if path_filter or since_commit:
        filtered_commits = {h: data for h, data in commits.items() if h in hashes}
        for data in filtered_commits.values():
            data['parents'] = [p for p in data['parents'] if p in filtered_commits]
        commits = filtered_commits

    return commits

def get_all_tags() -> Dict[str, Tuple[str, bool]]:
    tags = {}
    refs = run_git('show-ref', '--tags')
    if not refs:
        return tags
    for ref in refs.splitlines():
        if not ref:
            continue
        parts = ref.split()
        if len(parts) != 2:
            continue
        obj_hash, ref_name = parts
        tag_name = ref_name[len('refs/tags/'):]
        obj_type = run_git('cat-file', '-t', obj_hash)
        if obj_type == 'commit':
            tags[tag_name] = (obj_hash, False)
        elif obj_type == 'tag':
            tags[tag_name] = (obj_hash, True)
    return tags

def get_annotated_tag_target(tag_hash: str) -> str:
    content = run_git('cat-file', '-p', tag_hash)
    if not content:
        return ""
    for line in content.splitlines():
        if line.startswith('object '):
            return line[7:]
    return ""

def get_branches() -> Dict[str, str]:
    branches = {}
    output = run_git('branch', '--format=%(refname:short) %(objectname)')
    if not output:
        return branches
    for line in output.splitlines():
        if not line:
            continue
        parts = line.split()
        if len(parts) == 2:
            name, commit_hash = parts
            branches[name] = commit_hash
    return branches

def get_head() -> Optional[str]:
    head = run_git('rev-parse', 'HEAD')
    return head if head else None

# ----------------------------------------------------------------------
#  Сворачивание цепочек
# ----------------------------------------------------------------------

def compute_linear_chains(commits: Dict[str, Dict]) -> Dict[str, str]:
    children = defaultdict(list)
    for h, data in commits.items():
        for p in data["parents"]:
            children[p].append(h)

    important = set()
    for h, data in commits.items():
        if len(data["parents"]) != 1:
            important.add(h)
        if len(children.get(h, [])) != 1:
            important.add(h)

    branches = get_branches()
    for branch_hash in branches.values():
        if branch_hash in commits:
            important.add(branch_hash)
    tags = get_all_tags()
    for _, (target, is_anno) in tags.items():
        if is_anno:
            target = get_annotated_tag_target(target)
        if target in commits:
            important.add(target)
    head = get_head()
    if head and head in commits:
        important.add(head)

    mapping = {}
    for h in commits:
        if h in important:
            mapping[h] = h
            continue
        current = h
        chain = []
        while current not in important:
            chain.append(current)
            child_list = children.get(current, [])
            if len(child_list) == 1:
                current = child_list[0]
            else:
                break
        end = current
        for c in chain:
            mapping[c] = end
    for h in commits:
        if h not in mapping:
            mapping[h] = h
    return mapping

def build_collapsed_graph(commits: Dict[str, Dict], mapping: Dict[str, str]):
    groups = defaultdict(list)
    for orig, collapsed in mapping.items():
        groups[collapsed].append(orig)

    nodes = {}
    collapsed_groups = {}
    for coll_id, orig_list in groups.items():
        collapsed_groups[coll_id] = orig_list
        if len(orig_list) == 1:
            data = commits[coll_id]
            label = f"{coll_id[:7]}\n{data['message'][:20]}"
            title = f"Hash: {coll_id}\nAuthor: {data['author_name']}\nDate: {data['date_str']}\nMessage: {data['message']}"
            group = "commit"
            shape = "ellipse"
            color_bg = "#97C2FC"
        else:
            first = orig_list[0]
            last = orig_list[-1]
            count = len(orig_list)
            first_msg = commits[first]['message'][:20]
            label = f"{count} commits\n{first_msg}..."
            title = f"Collapsed chain of {count} commits\nFrom {first[:7]} to {last[:7]}"
            group = "collapsed"
            shape = "box"
            color_bg = "#D3D3D3"
        nodes[coll_id] = {
            "id": coll_id,
            "label": label,
            "title": title,
            "group": group,
            "shape": shape,
            "color": {"background": color_bg, "border": "#2c3e50"},
            "font": {"size": 12},
            "collapsed_hashes": orig_list
        }
    edges = set()
    for orig, data in commits.items():
        from_node = mapping[orig]
        for p in data["parents"]:
            to_node = mapping[p]
            if from_node != to_node:
                edges.add((from_node, to_node))
    return nodes, list(edges), collapsed_groups

def compute_statistics(commits: Dict[str, Dict]) -> Dict:
    total = len(commits)
    authors = Counter()
    date_counts = Counter()
    for data in commits.values():
        authors[data['author_name']] += 1
        date = data['date_str'].split()[0]
        date_counts[date] += 1
    top_authors = authors.most_common(10)
    sorted_dates = sorted(date_counts.items())
    return {
        "total_commits": total,
        "top_authors": [{"name": name, "count": cnt} for name, cnt in top_authors],
        "dates": [date for date, _ in sorted_dates],
        "counts": [cnt for _, cnt in sorted_dates]
    }

# ----------------------------------------------------------------------
#  HTTP-сервер
# ----------------------------------------------------------------------

class GitAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('git_viz_live.html', 'rb') as f:
                self.wfile.write(f.read())
        elif path.startswith('/api/commit/'):
            commit_hash = path.split('/')[-1]
            self.send_commit_info(commit_hash)
        elif path.startswith('/api/diff/'):
            parts = path.split('/')
            if len(parts) >= 5:
                commit_hash = parts[3]
                filename = unquote('/'.join(parts[4:]))
                self.send_file_diff(commit_hash, filename)
            else:
                self.send_error(400)
        else:
            self.send_error(404)

    def send_commit_info(self, commit_hash):
        try:
            output = run_git('show', '--stat', '--format=', commit_hash)
            files = []
            for line in output.splitlines():
                if '|' in line:
                    parts = line.split('|')
                    filename = parts[0].strip()
                    changes = parts[1].strip()
                    files.append({"filename": filename, "changes": changes})
            shortstat = run_git('show', '--shortstat', '--format=', commit_hash)
            self.send_json({"hash": commit_hash, "files": files, "shortstat": shortstat})
        except Exception as e:
            self.send_json({"error": str(e)})

    def send_file_diff(self, commit_hash, filename):
        try:
            parent = run_git('rev-parse', f'{commit_hash}^')
            if parent:
                cmd = ['diff', parent, commit_hash, '--', filename]
            else:
                cmd = ['show', commit_hash, '--', filename]
            output = run_git(*cmd)
            self.send_json({"filename": filename, "diff": output if output else "No changes"})
        except Exception as e:
            self.send_json({"error": str(e)})

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(('localhost', PORT), GitAPIHandler)
    print(f"Сервер запущен на http://localhost:{PORT}")
    server.serve_forever()

# ----------------------------------------------------------------------
#  Генерация HTML (улучшенный интерфейс)
# ----------------------------------------------------------------------

def generate_html(nodes: Dict[str, dict], edges: List[tuple],
                  collapsed_groups: Dict[str, List[str]],
                  all_commits: Dict[str, Dict],
                  statistics: Dict,
                  output_file: str,
                  port: int):
    nodes_list = list(nodes.values())
    edges_list = [{"from": u, "to": v} for u, v in edges]
    commits_data = {h: {"hash": h, "message": data['message'], "author": data['author_name'],
                        "date": data['date_str'], "parents": data['parents']}
                    for h, data in all_commits.items()}

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Git Repository Visualisation – Ultimate</title>
    <script src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; overflow: hidden; }}
        /* Панели фиксированной ширины */
        #sidebar {{
            position: absolute; top: 0; left: 0; width: 320px; height: 100vh;
            background: rgba(30,30,40,0.95); color: #f0f0f0; backdrop-filter: blur(8px);
            z-index: 20; padding: 15px; overflow-y: auto; box-shadow: 2px 0 12px rgba(0,0,0,0.3);
            transition: transform 0.3s ease; transform: translateX(0);
        }}
        #sidebar.collapsed {{ transform: translateX(-100%); }}
        #rightPanel {{
            position: absolute; top: 0; right: 0; width: 360px; height: 100vh;
            background: rgba(40,40,50,0.98); color: #f0f0f0; backdrop-filter: blur(8px);
            z-index: 20; padding: 15px; overflow-y: auto; box-shadow: -2px 0 12px rgba(0,0,0,0.3);
            transition: transform 0.3s ease; transform: translateX(0);
            border-left: 1px solid #555;
        }}
        #rightPanel.collapsed {{ transform: translateX(100%); }}
        /* Граф занимает всё оставшееся пространство */
        #network {{
            position: absolute;
            top: 0;
            left: 320px;
            right: 360px;
            bottom: 0;
            background: #fafafa;
            transition: left 0.3s ease, right 0.3s ease;
        }}
        /* При сворачивании левой панели */
        body.sidebar-collapsed #network {{
            left: 0;
        }}
        /* При сворачивании правой панели */
        body.rightpanel-collapsed #network {{
            right: 0;
        }}
        .toggle-btn {{
            position: absolute;
            background: #2c3e50; color: white; border: none;
            cursor: pointer; z-index: 25;
            font-size: 18px;
            transition: 0.2s;
        }}
        #toggleSidebar {{
            left: 320px; top: 20px;
            padding: 8px 12px;
            border-radius: 0 8px 8px 0;
        }}
        body.sidebar-collapsed #toggleSidebar {{
            left: 0;
        }}
        #toggleRightPanel {{
            right: 360px; top: 20px;
            padding: 8px 12px;
            border-radius: 8px 0 0 8px;
        }}
        body.rightpanel-collapsed #toggleRightPanel {{
            right: 0;
        }}
        /* Информация о коммите – компактно */
        #commitInfo {{
            font-size: 13px;
            background: #2c2c3a;
            padding: 8px;
            border-radius: 6px;
            margin-bottom: 10px;
            max-height: 200px;
            overflow-y: auto;
        }}
        #commitInfo p {{
            margin: 4px 0;
        }}
        .file-list {{
            list-style: none;
            margin-top: 5px;
            max-height: calc(100vh - 400px);
            overflow-y: auto;
        }}
        .file-list li {{
            padding: 5px;
            border-bottom: 1px solid #555;
            cursor: pointer;
            font-size: 12px;
        }}
        .file-list li:hover {{
            background: #2c3e50;
        }}
        .file-stats {{
            color: #8bc34a;
            float: right;
        }}
        .modal {{
            display: none; position: fixed; top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}
        .modal-content {{
            background: #1e1e1e; color: #d4d4d4;
            padding: 20px; border-radius: 12px;
            width: 80%; max-width: 900px; max-height: 80%;
            overflow: auto;
        }}
        pre {{ background: #2d2d2d; padding: 10px; border-radius: 6px; overflow-x: auto; }}
        .close-modal {{ float: right; cursor: pointer; font-size: 24px; color: #fff; }}
        button {{ background: #3498db; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }}
        button:hover {{ background: #2980b9; }}
        .author-list {{ list-style: none; margin-top: 5px; max-height: 150px; overflow-y: auto; }}
        .author-list li {{ margin: 5px 0; font-size: 0.85rem; }}
        .filter-group {{ margin: 15px 0; }}
        .filter-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
        select, input {{ width: 100%; padding: 5px; border-radius: 4px; border: none; }}
    </style>
</head>
<body>
<div id="sidebar">
    <h2>📊 Статистика</h2>
    <p>Всего коммитов: <span class="stat-number">{statistics['total_commits']}</span></p>
    <h3>🏆 Топ авторов</h3>
    <ul class="author-list" id="topAuthors"></ul>
    <h3>📅 Коммиты по дням</h3>
    <canvas id="histogram" width="280" height="150" style="background: #fff; border-radius: 6px;"></canvas>
    <h3>🔍 Фильтры</h3>
    <div class="filter-group"><label>👤 Автор</label><select id="filterAuthor"><option value="">Все</option></select></div>
    <div class="filter-group"><label>📆 Начиная с даты</label><input type="date" id="filterDateFrom"></div>
    <div class="filter-group"><label>📆 По дату</label><input type="date" id="filterDateTo"></div>
    <button id="applyFilters">Применить фильтр</button>
    <button id="resetFilters">Сбросить</button>
    <button id="exportPNG">📸 Экспорт PNG</button>
    <button id="clearHighlight">✨ Снять подсветку</button>
</div>
<button id="toggleSidebar" class="toggle-btn">☰</button>

<div id="rightPanel">
    <h2>📄 Информация о коммите</h2>
    <div id="commitInfo">Нажмите на коммит, чтобы увидеть детали</div>
    <h3>📁 Изменённые файлы</h3>
    <ul id="fileList" class="file-list"></ul>
</div>
<button id="toggleRightPanel" class="toggle-btn">❯</button>

<div id="network"></div>

<div id="diffModal" class="modal">
    <div class="modal-content">
        <span class="close-modal">&times;</span>
        <h3 id="diffTitle">Diff</h3>
        <pre id="diffContent"><code></code></pre>
    </div>
</div>

<script>
    var allNodes = {json.dumps(nodes_list, indent=2)};
    var allEdges = {json.dumps(edges_list, indent=2)};
    var collapsedGroups = {json.dumps(collapsed_groups)};
    var commitsData = {json.dumps(commits_data)};
    var statistics = {json.dumps(statistics)};
    var API_PORT = {port};

    var nodesDataSet = new vis.DataSet(allNodes);
    var edgesDataSet = new vis.DataSet(allEdges);
    var network;
    var currentAuthorFilter = "", currentDateFrom = "", currentDateTo = "";

    // Управление сворачиванием панелей с обновлением класса body
    function toggleSidebar() {{
        var sidebar = document.getElementById("sidebar");
        sidebar.classList.toggle("collapsed");
        if (sidebar.classList.contains("collapsed")) {{
            document.body.classList.add("sidebar-collapsed");
        }} else {{
            document.body.classList.remove("sidebar-collapsed");
        }}
        setTimeout(() => network.fit(), 100);
    }}
    function toggleRightPanel() {{
        var panel = document.getElementById("rightPanel");
        panel.classList.toggle("collapsed");
        if (panel.classList.contains("collapsed")) {{
            document.body.classList.add("rightpanel-collapsed");
            document.getElementById("toggleRightPanel").innerText = "◀";
        }} else {{
            document.body.classList.remove("rightpanel-collapsed");
            document.getElementById("toggleRightPanel").innerText = "❯";
        }}
        setTimeout(() => network.fit(), 100);
    }}

    function saveState() {{
        var state = {{ author: currentAuthorFilter, dateFrom: currentDateFrom, dateTo: currentDateTo, collapsedGroups: collapsedGroups }};
        localStorage.setItem('gitVizState', JSON.stringify(state));
    }}
    function loadState() {{
        var saved = localStorage.getItem('gitVizState');
        if (saved) {{
            try {{
                var state = JSON.parse(saved);
                currentAuthorFilter = state.author || "";
                currentDateFrom = state.dateFrom || "";
                currentDateTo = state.dateTo || "";
                document.getElementById("filterAuthor").value = currentAuthorFilter;
                document.getElementById("filterDateFrom").value = currentDateFrom;
                document.getElementById("filterDateTo").value = currentDateTo;
                applyFilters();
            }} catch(e) {{}}
        }}
    }}

    function initGraph() {{
        var container = document.getElementById('network');
        var data = {{ nodes: nodesDataSet, edges: edgesDataSet }};
        var options = {{
            nodes: {{ size: 25, font: {{ size: 12, face: 'monospace' }}, borderWidth: 1, shadow: true }},
            edges: {{ arrows: {{ to: {{ enabled: true, scaleFactor: 0.8 }} }}, smooth: {{ type: 'cubicBezier' }} }},
            physics: {{ stabilization: true, barnesHut: {{ gravitationalConstant: -2000 }} }},
            interaction: {{ hover: true, tooltipDelay: 100 }}
        }};
        network = new vis.Network(container, data, options);
        network.on("click", function(params) {{
            if (params.nodes.length === 1) {{
                var nodeId = params.nodes[0];
                var node = nodesDataSet.get(nodeId);
                if (node && node.group === "collapsed") {{
                    showExpandModal(nodeId);
                }} else if (node && node.group === "commit") {{
                    highlightPath(nodeId);
                    loadCommitInfo(nodeId);
                }}
            }}
        }});
    }}

    // Функции highlightPath, clearHighlight, exportPNG, expandCollapsedNode, applyFilters, resetFilters, renderStatistics, showExpandModal
    // (они же из предыдущей версии, но для краткости оставлю как есть)
    function highlightPath(commitId) {{
        var pathNodes = new Set();
        var queue = [commitId];
        var visited = new Set();
        while (queue.length) {{
            var current = queue.shift();
            if (visited.has(current)) continue;
            visited.add(current);
            pathNodes.add(current);
            var commit = commitsData[current];
            if (commit && commit.parents) {{
                for (var p of commit.parents) {{
                    if (!visited.has(p)) queue.push(p);
                }}
            }}
        }}
        var allCurrentNodes = nodesDataSet.get();
        for (var n of allCurrentNodes) {{
            nodesDataSet.update([{{ id: n.id, color: n.originalColor || n.color, font: {{ size: 12 }} }}]);
        }}
        for (var id of pathNodes) {{
            var node = nodesDataSet.get(id);
            if (node) {{
                if (!node.originalColor) node.originalColor = node.color;
                nodesDataSet.update([{{ id: id, color: {{ background: "#FFD966", border: "#B8860B" }}, font: {{ size: 14, bold: true }} }}]);
            }}
        }}
        network.fit({{ nodes: Array.from(pathNodes), animation: true }});
    }}
    function clearHighlight() {{
        var allCurrentNodes = nodesDataSet.get();
        for (var n of allCurrentNodes) {{
            var origColor = n.originalColor || n.color;
            nodesDataSet.update([{{ id: n.id, color: origColor, font: {{ size: 12 }} }}]);
        }}
    }}
    function exportPNG() {{
        var canvas = document.querySelector("#network canvas");
        if (canvas) {{
            var link = document.createElement('a');
            link.download = 'git_graph.png';
            link.href = canvas.toDataURL();
            link.click();
        }} else {{
            alert("Canvas not found");
        }}
    }}
    var currentCollapsedId = null;
    function showExpandModal(collapsedId) {{
        currentCollapsedId = collapsedId;
        var hashes = collapsedGroups[collapsedId] || [];
        var listHtml = "";
        for (var h of hashes) {{
            var commit = commitsData[h];
            if (commit) {{
                listHtml += `<li><b>${{h.substring(0,7)}}</b> ${{commit.author}} – ${{commit.message.substring(0,50)}}</li>`;
            }} else {{
                listHtml += `<li>${{h.substring(0,7)}}</li>`;
            }}
        }}
        document.getElementById("expandCommitList").innerHTML = listHtml;
        document.getElementById("expandModal").style.display = "flex";
    }}
    function expandCollapsedNode(collapsedId) {{
        var hashes = collapsedGroups[collapsedId] || [];
        if (hashes.length <= 1) return;
        nodesDataSet.remove(collapsedId);
        for (var h of hashes) {{
            var commit = commitsData[h];
            if (!commit) continue;
            var label = `${{h.substring(0,7)}}\\n${{commit.message.substring(0,20)}}`;
            var title = `Hash: ${{h}}\\nAuthor: ${{commit.author}}\\nDate: ${{commit.date}}\\nMessage: ${{commit.message}}`;
            nodesDataSet.add({{
                id: h, label: label, title: title, group: "commit", shape: "ellipse",
                color: {{ background: "#97C2FC", border: "#2c3e50" }}, font: {{ size: 12 }}
            }});
        }}
        var allEdges = edgesDataSet.get();
        var toRemove = [];
        for (var e of allEdges) {{
            if (e.from === collapsedId || e.to === collapsedId) toRemove.push(e.id);
        }}
        edgesDataSet.remove(toRemove);
        var newEdges = [];
        for (var h of hashes) {{
            var commit = commitsData[h];
            if (commit && commit.parents) {{
                for (var p of commit.parents) {{
                    if (hashes.includes(p) || nodesDataSet.get(p)) {{
                        newEdges.push({{ from: h, to: p }});
                    }} else {{
                        if (!nodesDataSet.get(p) && !collapsedGroups[p]) {{
                            nodesDataSet.add({{ id: p, label: p.substring(0,7), shape: "point", size: 5 }});
                        }}
                        newEdges.push({{ from: h, to: p }});
                    }}
                }}
            }}
        }}
        edgesDataSet.add(newEdges);
        delete collapsedGroups[collapsedId];
        network.fit();
        saveState();
    }}
    function applyFilters() {{
        currentAuthorFilter = document.getElementById("filterAuthor").value;
        currentDateFrom = document.getElementById("filterDateFrom").value;
        currentDateTo = document.getElementById("filterDateTo").value;
        var allCurrentNodes = nodesDataSet.get();
        for (var node of allCurrentNodes) {{
            var visible = true;
            if (node.group === "commit") {{
                var commit = commitsData[node.id];
                if (commit) {{
                    if (currentAuthorFilter && commit.author !== currentAuthorFilter) visible = false;
                    if (currentDateFrom && commit.date < currentDateFrom) visible = false;
                    if (currentDateTo && commit.date > currentDateTo) visible = false;
                }}
            }} else if (node.group === "collapsed") {{
                var hashes = collapsedGroups[node.id] || [node.id];
                var anyMatch = false;
                for (var h of hashes) {{
                    var c = commitsData[h];
                    if (c) {{
                        if (currentAuthorFilter && c.author !== currentAuthorFilter) continue;
                        if (currentDateFrom && c.date < currentDateFrom) continue;
                        if (currentDateTo && c.date > currentDateTo) continue;
                        anyMatch = true;
                        break;
                    }}
                }}
                visible = anyMatch;
            }}
            nodesDataSet.update([{{ id: node.id, hidden: !visible }}]);
        }}
        saveState();
    }}
    function resetFilters() {{
        document.getElementById("filterAuthor").value = "";
        document.getElementById("filterDateFrom").value = "";
        document.getElementById("filterDateTo").value = "";
        currentAuthorFilter = "";
        currentDateFrom = "";
        currentDateTo = "";
        applyFilters();
    }}
    function renderStatistics() {{
        var topHtml = "";
        for (var a of statistics.top_authors) topHtml += `<li>${{a.name}}: ${{a.count}} коммитов</li>`;
        document.getElementById("topAuthors").innerHTML = topHtml;
        var ctx = document.getElementById('histogram').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: statistics.dates.slice(-30),
                datasets: [{{ label: 'Коммиты', data: statistics.counts.slice(-30), backgroundColor: '#3498db' }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: true }}
        }});
        var authorSelect = document.getElementById("filterAuthor");
        var authorsSet = new Set();
        for (var h in commitsData) authorsSet.add(commitsData[h].author);
        var sortedAuthors = Array.from(authorsSet).sort();
        for (var a of sortedAuthors) {{
            var option = document.createElement("option");
            option.value = a; option.text = a;
            authorSelect.appendChild(option);
        }}
    }}
    function loadCommitInfo(commitHash) {{
        fetch(`/api/commit/${{commitHash}}`)
            .then(res => res.json())
            .then(data => {{
                if (data.error) {{
                    document.getElementById("commitInfo").innerHTML = `<p>Ошибка: ${{data.error}}</p>`;
                    return;
                }}
                var commit = commitsData[commitHash];
                var infoHtml = `<p><strong>Хеш:</strong> ${{commit.hash.substring(0,7)}}</p>
                                <p><strong>Автор:</strong> ${{commit.author}}</p>
                                <p><strong>Дата:</strong> ${{commit.date}}</p>
                                <p><strong>Сообщение:</strong> ${{commit.message}}</p>
                                <p><strong>Статистика:</strong> ${{data.shortstat || '—'}}</p>`;
                document.getElementById("commitInfo").innerHTML = infoHtml;
                var fileListHtml = "";
                for (var file of data.files) {{
                    fileListHtml += `<li data-filename="${{encodeURIComponent(file.filename)}}" data-commit="${{commitHash}}">
                                        ${{file.filename}} <span class="file-stats">${{file.changes}}</span>
                                     </li>`;
                }}
                document.getElementById("fileList").innerHTML = fileListHtml;
                document.querySelectorAll("#fileList li").forEach(li => {{
                    li.addEventListener("click", (e) => {{
                        e.stopPropagation();
                        var filename = decodeURIComponent(li.dataset.filename);
                        var chash = li.dataset.commit;
                        showDiff(chash, filename);
                    }});
                }});
            }})
            .catch(err => {{
                document.getElementById("commitInfo").innerHTML = `<p>Ошибка загрузки: ${{err.message}}</p>`;
            }});
    }}
    function showDiff(commitHash, filename) {{
        fetch(`/api/diff/${{commitHash}}/${{encodeURIComponent(filename)}}`)
            .then(res => res.json())
            .then(data => {{
                document.getElementById("diffTitle").innerText = `Diff для ${{filename}} (коммит ${{commitHash.substring(0,7)}})`;
                var diffText = data.diff || "Нет изменений";
                var codeBlock = document.getElementById("diffContent");
                codeBlock.innerHTML = `<code class="diff">${{escapeHtml(diffText)}}</code>`;
                document.getElementById("diffModal").style.display = "flex";
                hljs.highlightElement(codeBlock);
            }});
    }}
    function escapeHtml(text) {{
        return text.replace(/[&<>]/g, function(m) {{
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        }});
    }}

    // Привязка обработчиков
    document.getElementById("toggleSidebar").onclick = toggleSidebar;
    document.getElementById("toggleRightPanel").onclick = toggleRightPanel;
    document.getElementById("applyFilters").onclick = applyFilters;
    document.getElementById("resetFilters").onclick = resetFilters;
    document.getElementById("exportPNG").onclick = exportPNG;
    document.getElementById("clearHighlight").onclick = clearHighlight;
    document.querySelector(".close-modal").onclick = () => document.getElementById("diffModal").style.display = "none";

    // Создаём модальное окно для разворачивания
    var expandModalDiv = document.createElement('div');
    expandModalDiv.id = "expandModal";
    expandModalDiv.className = "modal";
    expandModalDiv.innerHTML = `<div class="modal-content"><span class="close-modal">&times;</span><h3>Развернуть цепочку</h3><ul id="expandCommitList"></ul><button id="confirmExpand">Развернуть</button><button id="cancelExpand">Отмена</button></div>`;
    document.body.appendChild(expandModalDiv);
    document.getElementById("confirmExpand").onclick = () => {{
        if (currentCollapsedId) expandCollapsedNode(currentCollapsedId);
        document.getElementById("expandModal").style.display = "none";
    }};
    document.getElementById("cancelExpand").onclick = () => document.getElementById("expandModal").style.display = "none";
    document.querySelectorAll("#expandModal .close-modal").forEach(el => el.onclick = () => document.getElementById("expandModal").style.display = "none");

    // Инициализация
    initGraph();
    renderStatistics();
    loadState();
    // Начальное состояние панелей (развёрнуты)
    document.body.classList.remove("sidebar-collapsed", "rightpanel-collapsed");
</script>
</body>
</html>"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Сохранён HTML: {output_file}")

# ----------------------------------------------------------------------
#  main
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--max-commits', type=int, default=0)
    parser.add_argument('--path', type=str, default='')
    parser.add_argument('--since', type=str, default='')
    parser.add_argument('--no-server', action='store_true')
    parser.add_argument('--port', type=int, default=8888)
    parser.add_argument('--output', default='git_viz_live.html')
    args = parser.parse_args()

    if not os.path.isdir('.git'):
        print("Ошибка: не найден .git")
        sys.exit(1)

    since_commit = args.since
    if since_commit:
        resolved = run_git('rev-parse', since_commit)
        if resolved:
            since_commit = resolved
            print(f"Начальный коммит: {since_commit[:7]}")
        else:
            print(f"Предупреждение: {args.since} не найден")
            since_commit = ""

    print("Загрузка коммитов...")
    all_commits = get_all_commits(args.max_commits, args.path, since_commit)
    if not all_commits:
        print("Нет коммитов.")
        return

    if not args.full:
        print("Сворачивание цепочек...")
        mapping = compute_linear_chains(all_commits)
    else:
        mapping = {h: h for h in all_commits}

    print("Построение графа...")
    nodes, edges, collapsed_groups = build_collapsed_graph(all_commits, mapping)

    print("Статистика...")
    statistics = compute_statistics(all_commits)

    print("Генерация HTML...")
    generate_html(nodes, edges, collapsed_groups, all_commits, statistics, args.output, args.port)

    if not args.no_server:
        print(f"Запуск сервера на http://localhost:{args.port}")
        threading.Thread(target=run_server, daemon=True).start()
        webbrowser.open(f"http://localhost:{args.port}")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("Сервер остановлен.")

if __name__ == "__main__":
    main()