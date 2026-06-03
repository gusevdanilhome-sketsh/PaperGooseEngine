#!/usr/bin/env python3
"""
Ультимативная визуализация Git-хранилища.
Расширенная версия с:
- полной информацией о коммитах (автор, дата)
- боковой панелью со статистикой (топ авторов, гистограмма)
- возможностью разворачивать свёрнутые цепочки
- фильтрацией по автору и дате
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
#  Вспомогательные функции для работы с Git (кроссплатформенно)
# ----------------------------------------------------------------------

def run_git(*args):
    """Выполняет git команду и возвращает stdout (текст в UTF-8)."""
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

def get_all_commits() -> Dict[str, Dict]:
    """
    Возвращает подробную информацию о каждом коммите:
    {
        hash: {
            "parents": [list],
            "message": str,
            "author": str,
            "date_timestamp": int,
            "date_str": str,
            "author_name": str (чистое имя)
        }
    }
    """
    hashes_raw = run_git('rev-list', '--all')
    if not hashes_raw:
        print("Не удалось получить список коммитов.")
        return {}
    hashes = hashes_raw.splitlines()
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
                # формат: "author Name Surname <email> 1234567890 +0300"
                parts = line.split()
                if len(parts) >= 5:
                    # последние два - timestamp и timezone
                    timestamp = parts[-2]
                    tz = parts[-1]
                    date_timestamp = int(timestamp)
                    dt = datetime.fromtimestamp(date_timestamp)
                    date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    # имя автора - всё между "author " и "<"
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
    """Возвращает {имя_тега: (хеш, является_аннотированным)}."""
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
    """Для аннотированного тега возвращает хеш коммита."""
    content = run_git('cat-file', '-p', tag_hash)
    if not content:
        return ""
    for line in content.splitlines():
        if line.startswith('object '):
            return line[7:]
    return ""

def get_branches() -> Dict[str, str]:
    """Возвращает {имя_ветки: хеш_коммита}."""
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
    """Возвращает хеш текущего HEAD."""
    head = run_git('rev-parse', 'HEAD')
    return head if head else None

# ----------------------------------------------------------------------
#  Сворачивание линейных цепочек
# ----------------------------------------------------------------------

def compute_linear_chains(commits: Dict[str, Dict]) -> Dict[str, str]:
    """Определяет маппинг коммит -> представитель группы."""
    # строим словарь детей
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

    # добавляем ветки и теги
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
    """
    Строит свёрнутые узлы и рёбра.
    Возвращает:
        nodes: dict {collapsed_id: {id, label, title, group, shape, color, collapsed_hashes (list)}}
        edges: list of (from, to)
        collapsed_groups: dict {collapsed_id: [original_hashes]}
    """
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
            # свёрнутая цепочка
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
            "collapsed_hashes": orig_list   # сохраняем для разворачивания
        }
    # рёбра
    edges = set()
    for orig, data in commits.items():
        from_node = mapping[orig]
        for p in data["parents"]:
            to_node = mapping[p]
            if from_node != to_node:
                edges.add((from_node, to_node))
    return nodes, list(edges), collapsed_groups

# ----------------------------------------------------------------------
#  Подготовка статистики
# ----------------------------------------------------------------------

def compute_statistics(commits: Dict[str, Dict]) -> Dict:
    """Возвращает статистику: всего коммитов, топ авторов, распределение по датам."""
    total = len(commits)
    authors = Counter()
    date_counts = Counter()
    for data in commits.values():
        authors[data['author_name']] += 1
        date = data['date_str'].split()[0]  # YYYY-MM-DD
        date_counts[date] += 1
    # топ-10 авторов
    top_authors = authors.most_common(10)
    # даты для гистограммы (отсортированные)
    sorted_dates = sorted(date_counts.items())
    return {
        "total_commits": total,
        "top_authors": [{"name": name, "count": cnt} for name, cnt in top_authors],
        "dates": [date for date, _ in sorted_dates],
        "counts": [cnt for _, cnt in sorted_dates]
    }

# ----------------------------------------------------------------------
#  Генерация HTML (с боковой панелью, фильтрацией и разворачиванием)
# ----------------------------------------------------------------------

def generate_html(nodes: Dict[str, dict], edges: List[tuple],
                  collapsed_groups: Dict[str, List[str]],
                  all_commits: Dict[str, Dict],
                  statistics: Dict,
                  output_file: str):
    """Генерирует интерактивный HTML с расширенными возможностями."""
    nodes_list = list(nodes.values())
    edges_list = [{"from": u, "to": v} for u, v in edges]

    # Подготовим данные о всех коммитах для разворачивания
    commits_data = {}
    for h, data in all_commits.items():
        commits_data[h] = {
            "hash": h,
            "message": data['message'],
            "author": data['author_name'],
            "date": data['date_str'],
            "parents": data['parents']
        }

    # Передаём collapsed_groups как словарь: collapsed_id -> список хешей
    # и commits_data для полной информации

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
        #sidebar.collapsed {
            transform: translateX(-100%);
        }
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
        button { background: #3498db; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin-top: 5px; }
        button:hover { background: #2980b9; }
        #network {
            width: 100%;
            height: 100vh;
            background: #fafafa;
        }
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
    </style>
</head>
<body>
<div id="sidebar">
    <h2>📊 Статистика</h2>
    <p>Всего коммитов: <span class="stat-number">{{TOTAL_COMMITS}}</span></p>
    <h3>🏆 Топ авторов</h3>
    <ul class="author-list" id="topAuthors">
        <!-- заполнится из JavaScript -->
    </ul>
    <h3>📅 Коммиты по дням</h3>
    <canvas id="histogram" width="280" height="150" style="background: #fff; border-radius: 6px;"></canvas>

    <h3>🔍 Фильтры</h3>
    <div class="filter-group">
        <label>👤 Автор</label>
        <select id="filterAuthor">
            <option value="">Все</option>
        </select>
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
    <button id="resetFilters" style="background:#7f8c8d;">Сбросить</button>
</div>
<button id="toggleSidebar">☰</button>

<div id="network"></div>

<!-- Модальное окно для разворачивания -->
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
    // Данные, переданные из Python
    var allNodes = {{NODES_JSON}};
    var allEdges = {{EDGES_JSON}};
    var collapsedGroups = {{COLLAPSED_GROUPS_JSON}};
    var commitsData = {{COMMITS_DATA_JSON}};
    var statistics = {{STATISTICS_JSON}};

    // Глобальные объекты vis
    var nodesDataSet = new vis.DataSet(allNodes);
    var edgesDataSet = new vis.DataSet(allEdges);
    var network;

    // Фильтры
    var currentAuthorFilter = "";
    var currentDateFrom = "";
    var currentDateTo = "";

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

        // Обработчик клика для разворачивания
        network.on("click", function(params) {
            if (params.nodes.length === 1) {
                var nodeId = params.nodes[0];
                var node = nodesDataSet.get(nodeId);
                if (node && node.group === "collapsed") {
                    showExpandModal(nodeId);
                }
            }
        });
    }

    // Модальное окно для разворачивания
    var currentCollapsedId = null;
    function showExpandModal(collapsedId) {
        currentCollapsedId = collapsedId;
        var hashes = collapsedGroups[collapsedId] || [];
        var listHtml = "";
        for (var i = 0; i < hashes.length; i++) {
            var h = hashes[i];
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
        // Удаляем свёрнутый узел
        nodesDataSet.remove(collapsedId);
        // Добавляем все коммиты из цепочки
        var addedNodes = [];
        for (var i = 0; i < hashes.length; i++) {
            var h = hashes[i];
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
        // Перестраиваем рёбра между этими коммитами и внешними связями
        // Сначала удалим старые рёбра, которые ссылались на collapsedId
        var allEdges = edgesDataSet.get();
        var toRemove = [];
        for (var j = 0; j < allEdges.length; j++) {
            var e = allEdges[j];
            if (e.from === collapsedId || e.to === collapsedId) {
                toRemove.push(e.id);
            }
        }
        edgesDataSet.remove(toRemove);
        // Добавим рёбра между коммитами внутри цепочки (используя исходные родительские связи)
        var newEdges = [];
        for (var k = 0; k < hashes.length; k++) {
            var h = hashes[k];
            var commit = commitsData[h];
            if (commit && commit.parents) {
                for (var p of commit.parents) {
                    // если родитель тоже в этой группе или уже существует как узел
                    if (hashes.includes(p) || nodesDataSet.get(p)) {
                        newEdges.push({ from: h, to: p });
                    } else {
                        // внешний родитель – нужно добавить ребро, даже если узла нет (добавим позже)
                        if (!nodesDataSet.get(p)) {
                            // добавим заглушку для внешнего родителя? но он может быть другим свёрнутым узлом
                            // проще добавить ребро, vis сам создаст узел? нет – нужно убедиться, что узел есть.
                            // В реальности внешний родитель может быть уже добавлен как свёрнутый узел или коммит.
                            if (!nodesDataSet.get(p) && !collapsedGroups[p]) {
                                // добавим как точку
                                nodesDataSet.add({ id: p, label: p.substring(0,7), shape: "point", size: 5 });
                            }
                        }
                        newEdges.push({ from: h, to: p });
                    }
                }
            }
        }
        // Добавляем также рёбра от внешних узлов к первому/последнему коммиту цепочки
        // (они уже частично покрываются родительскими связями)
        edgesDataSet.add(newEdges);
        // Обновляем collapsedGroups
        delete collapsedGroups[collapsedId];
        // Перезапустим физику
        network.fit();
    }

    // Обработчики модального окна
    document.getElementById("confirmExpand").onclick = function() {
        if (currentCollapsedId) {
            expandCollapsedNode(currentCollapsedId);
            document.getElementById("expandModal").style.display = "none";
        }
    };
    document.getElementById("cancelExpand").onclick = function() {
        document.getElementById("expandModal").style.display = "none";
    };
    document.querySelector(".close-modal").onclick = function() {
        document.getElementById("expandModal").style.display = "none";
    };

    // Статистика и фильтры
    function renderStatistics() {
        var topHtml = "";
        for (var a of statistics.top_authors) {
            topHtml += `<li>${a.name}: ${a.count} коммитов</li>`;
        }
        document.getElementById("topAuthors").innerHTML = topHtml;

        // Гистограмма
        var ctx = document.getElementById('histogram').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: statistics.dates.slice(-30), // последние 30 дней
                datasets: [{
                    label: 'Коммиты',
                    data: statistics.counts.slice(-30),
                    backgroundColor: '#3498db'
                }]
            },
            options: { responsive: true, maintainAspectRatio: true }
        });

        // Заполнить select авторов
        var authorSelect = document.getElementById("filterAuthor");
        var authorsSet = new Set();
        for (var h in commitsData) {
            authorsSet.add(commitsData[h].author);
        }
        var sortedAuthors = Array.from(authorsSet).sort();
        for (var a of sortedAuthors) {
            var option = document.createElement("option");
            option.value = a;
            option.text = a;
            authorSelect.appendChild(option);
        }
    }

    function applyFilters() {
        var author = document.getElementById("filterAuthor").value;
        var dateFrom = document.getElementById("filterDateFrom").value;
        var dateTo = document.getElementById("filterDateTo").value;

        // Фильтрация узлов: скрываем те, которые не подходят под критерии
        var allCurrentNodes = nodesDataSet.get();
        for (var node of allCurrentNodes) {
            var visible = true;
            if (node.group === "commit") {
                var commit = commitsData[node.id];
                if (commit) {
                    if (author && commit.author !== author) visible = false;
                    if (dateFrom && commit.date < dateFrom) visible = false;
                    if (dateTo && commit.date > dateTo) visible = false;
                }
            } else if (node.group === "collapsed") {
                // для свёрнутых: если хотя бы один коммит в группе подходит, показываем
                var hashes = collapsedGroups[node.id] || [node.id];
                var anyMatch = false;
                for (var h of hashes) {
                    var c = commitsData[h];
                    if (c) {
                        if (author && c.author !== author) continue;
                        if (dateFrom && c.date < dateFrom) continue;
                        if (dateTo && c.date > dateTo) continue;
                        anyMatch = true;
                        break;
                    }
                }
                visible = anyMatch;
            }
            nodesDataSet.update([{ id: node.id, hidden: !visible }]);
        }
    }

    function resetFilters() {
        document.getElementById("filterAuthor").value = "";
        document.getElementById("filterDateFrom").value = "";
        document.getElementById("filterDateTo").value = "";
        applyFilters();
    }

    // Боковая панель
    var sidebar = document.getElementById("sidebar");
    document.getElementById("toggleSidebar").onclick = function() {
        sidebar.classList.toggle("collapsed");
    };

    document.getElementById("applyFilters").onclick = applyFilters;
    document.getElementById("resetFilters").onclick = resetFilters;

    // Запуск
    initGraph();
    renderStatistics();
</script>
</body>
</html>"""
    # Замена плейсхолдеров
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
    parser.add_argument('--output', default='git_viz_advanced.html', help='Выходной HTML')
    args = parser.parse_args()

    if not os.path.isdir('.git'):
        print("Ошибка: не найден .git")
        sys.exit(1)

    print("Загрузка коммитов (это может занять время)...")
    all_commits = get_all_commits()
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