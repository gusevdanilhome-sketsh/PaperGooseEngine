#!/usr/bin/env python3
"""
Ультимативная визуализация Git-хранилища.
Расширенная версия с экспортом PNG, сохранением состояния, подсветкой пути.
"""

import subprocess
import json
import sys
import os
import argparse
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional

# ----------------------------------------------------------------------
#  Вспомогательные функции для работы с Git
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

def get_all_commits(max_commits: int = 0) -> Dict[str, Dict]:
    hashes_raw = run_git('rev-list', '--all')
    if not hashes_raw:
        return {}
    hashes = hashes_raw.splitlines()
    if max_commits > 0 and len(hashes) > max_commits:
        hashes = hashes[:max_commits]
        print(f"Ограничение: загружено только {max_commits} коммитов (используйте --max-commits=0 для всех)")
    print(f"Загружено коммитов: {len(hashes)}")

    commits = {}
    for h in hashes:
        if not h:
            continue
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
#  Сворачивание линейных цепочек
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
        important.add(branch_hash)
    tags = get_all_tags()
    for _, (target, is_anno) in tags.items():
        if is_anno:
            target = get_annotated_tag_target(target)
        important.add(target)
    head = get_head()
    if head:
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
#  Генерация HTML с расширенными функциями
# ----------------------------------------------------------------------

def generate_html(nodes: Dict[str, dict], edges: List[tuple],
                  collapsed_groups: Dict[str, List[str]],
                  all_commits: Dict[str, Dict],
                  statistics: Dict,
                  output_file: str):
    nodes_list = list(nodes.values())
    edges_list = [{"from": u, "to": v} for u, v in edges]

    commits_data = {}
    for h, data in all_commits.items():
        commits_data[h] = {
            "hash": h,
            "message": data['message'],
            "author": data['author_name'],
            "date": data['date_str'],
            "parents": data['parents']
        }

    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Git Repository Visualisation – Advanced</title>
    <script src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; overflow: hidden; }
        #sidebar {
            position: absolute;
            top: 0;
            left: 0;
            width: 320px;
            height: 100vh;
            background: rgba(30,30,40,0.95);
            color: #f0f0f0;
            backdrop-filter: blur(8px);
            z-index: 20;
            padding: 15px;
            overflow-y: auto;
            box-shadow: 2px 0 12px rgba(0,0,0,0.3);
            transition: transform 0.3s ease;
            transform: translateX(0);
        }
        #sidebar.collapsed { transform: translateX(-100%); }
        #toggleSidebar {
            position: absolute;
            left: 330px;
            top: 20px;
            background: #2c3e50;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 0 8px 8px 0;
            cursor: pointer;
            z-index: 25;
            font-size: 18px;
        }
        #sidebar h2 { font-size: 1.2rem; margin-bottom: 10px; border-bottom: 1px solid #aaa; }
        .stat-number { font-size: 1.5rem; font-weight: bold; color: #ffaa66; }
        .author-list { list-style: none; margin-top: 5px; }
        .author-list li { margin: 5px 0; font-size: 0.85rem; }
        .filter-group { margin: 15px 0; }
        .filter-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        select, input { width: 100%; padding: 5px; border-radius: 4px; border: none; }
        button { background: #3498db; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin-top: 5px; margin-right: 5px; }
        button:hover { background: #2980b9; }
        #network { width: 100%; height: 100vh; background: #fafafa; }
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.6);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: white;
            padding: 20px;
            border-radius: 12px;
            width: 500px;
            max-width: 80%;
            max-height: 70%;
            overflow: auto;
            color: #333;
        }
        .commit-list { list-style: none; margin: 10px 0; }
        .commit-list li { border-bottom: 1px solid #eee; padding: 6px 0; font-size: 12px; }
        .close-modal { float: right; cursor: pointer; font-size: 24px; }
        .highlighted { filter: drop-shadow(0 0 4px red); }
    </style>
</head>
<body>
<div id="sidebar">
    <h2>📊 Статистика</h2>
    <p>Всего коммитов: <span class="stat-number">{{TOTAL_COMMITS}}</span></p>
    <h3>🏆 Топ авторов</h3>
    <ul class="author-list" id="topAuthors"></ul>
    <h3>📅 Коммиты по дням</h3>
    <canvas id="histogram" width="280" height="150" style="background: #fff; border-radius: 6px;"></canvas>

    <h3>🔍 Фильтры</h3>
    <div class="filter-group">
        <label>👤 Автор</label>
        <select id="filterAuthor"><option value="">Все</option></select>
    </div>
    <div class="filter-group">
        <label>📆 Начиная с даты</label>
        <input type="date" id="filterDateFrom">
    </div>
    <div class="filter-group">
        <label>📆 По дату</label>
        <input type="date" id="filterDateTo">
    </div>
    <button id="applyFilters">Применить фильтр</button>
    <button id="resetFilters">Сбросить</button>
    <button id="exportPNG">📸 Экспорт PNG</button>
    <button id="clearHighlight">✨ Снять подсветку</button>
</div>
<button id="toggleSidebar">☰</button>
<div id="network"></div>

<div id="expandModal" class="modal">
    <div class="modal-content">
        <span class="close-modal">&times;</span>
        <h3>Развернуть цепочку коммитов</h3>
        <p>Коммиты в свёрнутой группе:</p>
        <ul id="expandCommitList" class="commit-list"></ul>
        <button id="confirmExpand">Развернуть все</button>
        <button id="cancelExpand">Отмена</button>
    </div>
</div>

<script>
    // Данные из Python
    var allNodes = {{NODES_JSON}};
    var allEdges = {{EDGES_JSON}};
    var collapsedGroups = {{COLLAPSED_GROUPS_JSON}};
    var commitsData = {{COMMITS_DATA_JSON}};
    var statistics = {{STATISTICS_JSON}};

    var nodesDataSet = new vis.DataSet(allNodes);
    var edgesDataSet = new vis.DataSet(allEdges);
    var network;
    var currentAuthorFilter = "", currentDateFrom = "", currentDateTo = "";

    // Сохранение состояния
    function saveState() {
        var state = {
            author: currentAuthorFilter,
            dateFrom: currentDateFrom,
            dateTo: currentDateTo,
            collapsedGroups: collapsedGroups,
            nodes: nodesDataSet.get()
        };
        localStorage.setItem('gitVizState', JSON.stringify(state));
    }

    function loadState() {
        var saved = localStorage.getItem('gitVizState');
        if (saved) {
            try {
                var state = JSON.parse(saved);
                currentAuthorFilter = state.author || "";
                currentDateFrom = state.dateFrom || "";
                currentDateTo = state.dateTo || "";
                document.getElementById("filterAuthor").value = currentAuthorFilter;
                document.getElementById("filterDateFrom").value = currentDateFrom;
                document.getElementById("filterDateTo").value = currentDateTo;
                applyFilters();
            } catch(e) {}
        }
    }

    // Инициализация графа
    function initGraph() {
        var container = document.getElementById('network');
        var data = { nodes: nodesDataSet, edges: edgesDataSet };
        var options = {
            nodes: { size: 25, font: { size: 12, face: 'monospace' }, borderWidth: 1, shadow: true },
            edges: { arrows: { to: { enabled: true, scaleFactor: 0.8 } }, smooth: { type: 'cubicBezier' } },
            physics: { stabilization: true, barnesHut: { gravitationalConstant: -2000 } },
            interaction: { hover: true, tooltipDelay: 100 }
        };
        network = new vis.Network(container, data, options);
        network.on("click", function(params) {
            if (params.nodes.length === 1) {
                var nodeId = params.nodes[0];
                var node = nodesDataSet.get(nodeId);
                if (node && node.group === "collapsed") {
                    showExpandModal(nodeId);
                } else if (node && node.group === "commit") {
                    highlightPath(nodeId);
                }
            }
        });
    }

    // Подсветка пути от коммита до корня (по родителям)
    function highlightPath(commitId) {
        var pathNodes = new Set();
        var queue = [commitId];
        var visited = new Set();
        while (queue.length) {
            var current = queue.shift();
            if (visited.has(current)) continue;
            visited.add(current);
            pathNodes.add(current);
            var commit = commitsData[current];
            if (commit && commit.parents) {
                for (var p of commit.parents) {
                    if (!visited.has(p)) queue.push(p);
                }
            }
        }
        // Сначала сбросим все выделения
        var allCurrentNodes = nodesDataSet.get();
        for (var n of allCurrentNodes) {
            nodesDataSet.update([{ id: n.id, color: n.originalColor || n.color, font: { size: 12 } }]);
        }
        // Выделим найденные узлы (сохраним оригинальные цвета)
        for (var id of pathNodes) {
            var node = nodesDataSet.get(id);
            if (node) {
                if (!node.originalColor) node.originalColor = node.color;
                nodesDataSet.update([{ id: id, color: { background: "#FFD966", border: "#B8860B" }, font: { size: 14, bold: true } }]);
            }
        }
        // Также выделим рёбра (опционально)
        network.fit({ nodes: Array.from(pathNodes), animation: true });
    }

    function clearHighlight() {
        var allCurrentNodes = nodesDataSet.get();
        for (var n of allCurrentNodes) {
            var origColor = n.originalColor || n.color;
            nodesDataSet.update([{ id: n.id, color: origColor, font: { size: 12 } }]);
        }
    }

    // Экспорт PNG
    function exportPNG() {
        var canvas = document.querySelector("#network canvas");
        if (canvas) {
            var link = document.createElement('a');
            link.download = 'git_graph.png';
            link.href = canvas.toDataURL();
            link.click();
        } else {
            alert("Не удалось найти canvas");
        }
    }

    // Разворачивание цепочки (как ранее)
    var currentCollapsedId = null;
    function showExpandModal(collapsedId) {
        currentCollapsedId = collapsedId;
        var hashes = collapsedGroups[collapsedId] || [];
        var listHtml = "";
        for (var h of hashes) {
            var commit = commitsData[h];
            if (commit) {
                listHtml += `<li><b>${h.substring(0,7)}</b> ${commit.author} – ${commit.message.substring(0,50)}</li>`;
            } else {
                listHtml += `<li>${h.substring(0,7)}</li>`;
            }
        }
        document.getElementById("expandCommitList").innerHTML = listHtml;
        document.getElementById("expandModal").style.display = "flex";
    }

    function expandCollapsedNode(collapsedId) {
        var hashes = collapsedGroups[collapsedId] || [];
        if (hashes.length <= 1) return;
        nodesDataSet.remove(collapsedId);
        var addedNodes = [];
        for (var h of hashes) {
            var commit = commitsData[h];
            if (!commit) continue;
            var label = `${h.substring(0,7)}\\n${commit.message.substring(0,20)}`;
            var title = `Hash: ${h}\\nAuthor: ${commit.author}\\nDate: ${commit.date}\\nMessage: ${commit.message}`;
            var newNode = {
                id: h,
                label: label,
                title: title,
                group: "commit",
                shape: "ellipse",
                color: { background: "#97C2FC", border: "#2c3e50" },
                font: { size: 12 }
            };
            nodesDataSet.add(newNode);
            addedNodes.push(h);
        }
        var allEdges = edgesDataSet.get();
        var toRemove = [];
        for (var e of allEdges) {
            if (e.from === collapsedId || e.to === collapsedId) toRemove.push(e.id);
        }
        edgesDataSet.remove(toRemove);
        var newEdges = [];
        for (var h of hashes) {
            var commit = commitsData[h];
            if (commit && commit.parents) {
                for (var p of commit.parents) {
                    if (hashes.includes(p) || nodesDataSet.get(p)) {
                        newEdges.push({ from: h, to: p });
                    } else {
                        if (!nodesDataSet.get(p) && !collapsedGroups[p]) {
                            nodesDataSet.add({ id: p, label: p.substring(0,7), shape: "point", size: 5 });
                        }
                        newEdges.push({ from: h, to: p });
                    }
                }
            }
        }
        edgesDataSet.add(newEdges);
        delete collapsedGroups[collapsedId];
        network.fit();
        saveState();
    }

    // Фильтрация
    function applyFilters() {
        currentAuthorFilter = document.getElementById("filterAuthor").value;
        currentDateFrom = document.getElementById("filterDateFrom").value;
        currentDateTo = document.getElementById("filterDateTo").value;
        var allCurrentNodes = nodesDataSet.get();
        for (var node of allCurrentNodes) {
            var visible = true;
            if (node.group === "commit") {
                var commit = commitsData[node.id];
                if (commit) {
                    if (currentAuthorFilter && commit.author !== currentAuthorFilter) visible = false;
                    if (currentDateFrom && commit.date < currentDateFrom) visible = false;
                    if (currentDateTo && commit.date > currentDateTo) visible = false;
                }
            } else if (node.group === "collapsed") {
                var hashes = collapsedGroups[node.id] || [node.id];
                var anyMatch = false;
                for (var h of hashes) {
                    var c = commitsData[h];
                    if (c) {
                        if (currentAuthorFilter && c.author !== currentAuthorFilter) continue;
                        if (currentDateFrom && c.date < currentDateFrom) continue;
                        if (currentDateTo && c.date > currentDateTo) continue;
                        anyMatch = true;
                        break;
                    }
                }
                visible = anyMatch;
            }
            nodesDataSet.update([{ id: node.id, hidden: !visible }]);
        }
        saveState();
    }

    function resetFilters() {
        document.getElementById("filterAuthor").value = "";
        document.getElementById("filterDateFrom").value = "";
        document.getElementById("filterDateTo").value = "";
        currentAuthorFilter = "";
        currentDateFrom = "";
        currentDateTo = "";
        applyFilters();
    }

    // Статистика
    function renderStatistics() {
        var topHtml = "";
        for (var a of statistics.top_authors) {
            topHtml += `<li>${a.name}: ${a.count} коммитов</li>`;
        }
        document.getElementById("topAuthors").innerHTML = topHtml;
        var ctx = document.getElementById('histogram').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: statistics.dates.slice(-30),
                datasets: [{ label: 'Коммиты', data: statistics.counts.slice(-30), backgroundColor: '#3498db' }]
            },
            options: { responsive: true, maintainAspectRatio: true }
        });
        var authorSelect = document.getElementById("filterAuthor");
        var authorsSet = new Set();
        for (var h in commitsData) authorsSet.add(commitsData[h].author);
        var sortedAuthors = Array.from(authorsSet).sort();
        for (var a of sortedAuthors) {
            var option = document.createElement("option");
            option.value = a;
            option.text = a;
            authorSelect.appendChild(option);
        }
    }

    // Обработчики событий
    document.getElementById("toggleSidebar").onclick = function() {
        document.getElementById("sidebar").classList.toggle("collapsed");
    };
    document.getElementById("applyFilters").onclick = applyFilters;
    document.getElementById("resetFilters").onclick = resetFilters;
    document.getElementById("exportPNG").onclick = exportPNG;
    document.getElementById("clearHighlight").onclick = clearHighlight;
    document.getElementById("confirmExpand").onclick = function() {
        if (currentCollapsedId) { expandCollapsedNode(currentCollapsedId); document.getElementById("expandModal").style.display = "none"; }
    };
    document.getElementById("cancelExpand").onclick = function() { document.getElementById("expandModal").style.display = "none"; };
    document.querySelector(".close-modal").onclick = function() { document.getElementById("expandModal").style.display = "none"; };

    // Запуск
    initGraph();
    renderStatistics();
    loadState();
</script>
</body>
</html>"""
    html_content = html_template.replace("{{NODES_JSON}}", json.dumps(nodes_list, indent=2))
    html_content = html_content.replace("{{EDGES_JSON}}", json.dumps(edges_list, indent=2))
    html_content = html_content.replace("{{COLLAPSED_GROUPS_JSON}}", json.dumps(collapsed_groups))
    html_content = html_content.replace("{{COMMITS_DATA_JSON}}", json.dumps(commits_data))
    html_content = html_content.replace("{{STATISTICS_JSON}}", json.dumps(statistics))
    html_content = html_content.replace("{{TOTAL_COMMITS}}", str(statistics['total_commits']))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Сохранён HTML: {output_file}")

# ----------------------------------------------------------------------
#  Основная функция
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='Не сворачивать цепочки')
    parser.add_argument('--max-commits', type=int, default=0, help='Максимальное число коммитов (0=все)')
    parser.add_argument('--output', default='git_viz_ultimate.html', help='Выходной HTML')
    args = parser.parse_args()

    if not os.path.isdir('.git'):
        print("Ошибка: не найден .git")
        sys.exit(1)

    print("Загрузка коммитов...")
    all_commits = get_all_commits(args.max_commits)
    if not all_commits:
        print("Нет коммитов")
        return

    if not args.full:
        print("Свёртывание линейных цепочек...")
        mapping = compute_linear_chains(all_commits)
    else:
        mapping = {h: h for h in all_commits}

    print("Построение графа...")
    nodes, edges, collapsed_groups = build_collapsed_graph(all_commits, mapping)

    print("Вычисление статистики...")
    statistics = compute_statistics(all_commits)

    print("Генерация HTML...")
    generate_html(nodes, edges, collapsed_groups, all_commits, statistics, args.output)

    print(f"Готово! Откройте {args.output} в браузере.")

if __name__ == "__main__":
    main()