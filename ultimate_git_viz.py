#!/usr/bin/env python3
"""
Ультимативная визуализация Git-хранилища.
Поддерживает сворачивание линейных цепочек, теги, ветки, HEAD.
Генерирует интерактивный HTML-граф (vis-network) и опционально DOT/PNG.
"""

import subprocess
import json
import sys
import os
import argparse
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional

# ----------------------------------------------------------------------
#  Вспомогательные функции для работы с Git (исправленные для Windows)
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
            # Не фатально — просто вернём пустую строку
            return ""
        return result.stdout.strip()
    except Exception:
        # fallback: без указания кодировки
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

def get_all_commits() -> Dict[str, Tuple[List[str], str, str, str]]:
    """Возвращает {хеш: (родители, сообщение, автор, дата)}."""
    hashes_raw = run_git('rev-list', '--all')
    if not hashes_raw:
        print("Не удалось получить список коммитов. Проверьте, что это Git-репозиторий.")
        return {}
    hashes = hashes_raw.splitlines()
    print(f"Найдено коммитов: {len(hashes)}")

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
        date = ""
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.startswith('parent '):
                parents.append(line[7:])
            elif line.startswith('author '):
                parts = line.split()
                if len(parts) >= 5:
                    date = ' '.join(parts[-2:])   # timestamp timezone
                    author = ' '.join(parts[1:-2])
            elif line == '':
                # сообщение начинается со следующей строки
                msg_lines = lines[i+1:]
                if msg_lines:
                    message = '\n'.join(msg_lines).strip()[:80]
                break
        commits[h] = (parents, message, author, date)
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
    """Для аннотированного тега возвращает хеш коммита, на который он указывает."""
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

def compute_linear_chains(commits: Dict[str, Tuple[List[str], str, str, str]]) -> Dict[str, str]:
    """Определяет маппинг коммит -> представитель группы (если цепочка сворачивается)."""
    # строим словарь детей
    children = defaultdict(list)
    for h, (parents, _, _, _) in commits.items():
        for p in parents:
            children[p].append(h)
    # важные коммиты
    important = set()
    for h in commits:
        if len(commits[h][0]) != 1:   # merge или корневой
            important.add(h)
        if len(children.get(h, [])) != 1:  # ветвление или лист
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
        # идём по цепочке вперёд (к детям)
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
    # оставшиеся (если что) – сами себе
    for h in commits:
        if h not in mapping:
            mapping[h] = h
    return mapping

def collapse_commits(commits: Dict[str, Tuple[List[str], str, str, str]],
                     mapping: Dict[str, str]) -> Tuple[Dict[str, dict], List[tuple]]:
    """Возвращает (узлы, рёбра) после сворачивания."""
    groups = defaultdict(list)
    for orig, collapsed in mapping.items():
        groups[collapsed].append(orig)

    nodes = {}
    for coll_id, orig_list in groups.items():
        if len(orig_list) == 1:
            parents, msg, author, date = commits[coll_id]
            label = f"{coll_id[:7]}\n{msg[:20]}"
            title = f"Hash: {coll_id}\nAuthor: {author}\nDate: {date}\nMessage: {msg}"
            group = "commit"
            shape = "ellipse"
            color_bg = "#97C2FC"
        else:
            first = orig_list[0]
            last = orig_list[-1]
            count = len(orig_list)
            _, first_msg, _, _ = commits[first]
            label = f"{count} commits\n{first_msg[:20]}..."
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
            "font": {"size": 12}
        }
    # рёбра
    edges = set()
    for orig, (parents, _, _, _) in commits.items():
        from_node = mapping[orig]
        for p in parents:
            to_node = mapping[p]
            if from_node != to_node:
                edges.add((from_node, to_node))
    return nodes, list(edges)

def add_tags_and_branches(nodes: Dict[str, dict], edges: List[tuple],
                          tags: Dict[str, Tuple[str, bool]],
                          branches: Dict[str, str],
                          head: Optional[str]) -> Tuple[Dict[str, dict], List[tuple]]:
    """Добавляет узлы для тегов (ромбы), веток (звёзды) и подсветку HEAD."""
    # Теги
    for tag_name, (target, is_anno) in tags.items():
        if is_anno:
            target = get_annotated_tag_target(target)
        tag_id = f"tag_{tag_name}"
        if tag_id not in nodes:
            nodes[tag_id] = {
                "id": tag_id,
                "label": tag_name,
                "title": f"Tag: {tag_name}\nPoints to: {target[:7]}",
                "group": "tag",
                "shape": "diamond",
                "color": {"background": "#90EE90", "border": "#2E8B57"},
                "font": {"size": 12}
            }
            edges.append((tag_id, target))
    # Ветки
    for branch_name, commit_hash in branches.items():
        branch_id = f"branch_{branch_name}"
        if branch_id not in nodes:
            nodes[branch_id] = {
                "id": branch_id,
                "label": branch_name,
                "title": f"Branch: {branch_name}\nPoints to: {commit_hash[:7]}",
                "group": "branch",
                "shape": "star",
                "color": {"background": "#FFD700", "border": "#DAA520"},
                "font": {"size": 12}
            }
            edges.append((branch_id, commit_hash))
    # HEAD — подсветка коммита
    if head and head in nodes:
        nodes[head]["color"] = {"background": "#FF6B6B", "border": "#C0392B"}
        if "title" in nodes[head]:
            nodes[head]["title"] += "\nHEAD"
    return nodes, edges

# ----------------------------------------------------------------------
#  Генерация HTML (vis-network)
# ----------------------------------------------------------------------

def generate_html(nodes: Dict[str, dict], edges: List[tuple], output_file: str):
    """Создаёт интерактивный HTML-файл с графом."""
    nodes_list = list(nodes.values())
    edges_list = [{"from": u, "to": v} for u, v in edges]

    # Шаблон HTML (полный)
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Git Repository Visualisation</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <style>
        body { margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; }
        #controls {
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            padding: 10px 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 10;
            font-size: 14px;
        }
        #search { padding: 5px; width: 200px; margin-right: 10px; }
        button { padding: 5px 10px; cursor: pointer; }
        #status {
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 10;
        }
        #network {
            width: 100%;
            height: 100vh;
            border: 1px solid lightgray;
        }
        .legend {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.2);
            z-index: 10;
        }
        .legend span {
            display: inline-block;
            width: 16px;
            height: 16px;
            margin-right: 4px;
            vertical-align: middle;
        }
    </style>
</head>
<body>
<div id="controls">
    <input type="text" id="search" placeholder="Search by label or hash...">
    <button onclick="searchNode()">Find</button>
    <button onclick="resetView()">Reset view</button>
</div>
<div id="status">Nodes: {{NODES_COUNT}}, Edges: {{EDGES_COUNT}}</div>
<div class="legend">
    <div><span style="background:#97C2FC; border-radius:50%;"></span> Commit</div>
    <div><span style="background:#90EE90; transform:rotate(45deg);"></span> Tag</div>
    <div><span style="background:#FFD700; clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);"></span> Branch</div>
    <div><span style="background:#D3D3D3;"></span> Collapsed chain</div>
    <div><span style="background:#FF6B6B; border-radius:50%;"></span> HEAD</div>
</div>
<div id="network"></div>
<script>
    var nodes = new vis.DataSet({{NODES_JSON}});
    var edges = new vis.DataSet({{EDGES_JSON}});
    var container = document.getElementById('network');
    var data = { nodes: nodes, edges: edges };
    var options = {
        nodes: {
            size: 25,
            font: { size: 12, face: 'monospace' },
            borderWidth: 1,
            shadow: true
        },
        edges: {
            arrows: { to: { enabled: true, scaleFactor: 0.8 } },
            color: { color: '#848484', highlight: '#000000' },
            smooth: { type: 'cubicBezier', roundness: 0.2 }
        },
        physics: {
            stabilization: true,
            barnesHut: { gravitationalConstant: -2000, centralGravity: 0.1 }
        },
        interaction: {
            hover: true,
            tooltipDelay: 100,
            zoomView: true,
            dragView: true
        },
        layout: { improvedLayout: true }
    };
    var network = new vis.Network(container, data, options);

    function searchNode() {
        var query = document.getElementById('search').value.toLowerCase();
        if (!query) return;
        var nodeIds = nodes.getIds();
        for (var i = 0; i < nodeIds.length; i++) {
            var node = nodes.get(nodeIds[i]);
            if (node.label && node.label.toLowerCase().includes(query)) {
                network.selectNodes([node.id]);
                network.focus(node.id, { scale: 1.5, animation: true });
                return;
            }
        }
        alert("Not found");
    }
    function resetView() {
        network.fit({ animation: true });
        network.unselectAll();
    }
</script>
</body>
</html>"""
    # Подстановка данных
    html_content = html_template.replace("{{NODES_JSON}}", json.dumps(nodes_list, indent=2))
    html_content = html_content.replace("{{EDGES_JSON}}", json.dumps(edges_list, indent=2))
    html_content = html_content.replace("{{NODES_COUNT}}", str(len(nodes_list)))
    html_content = html_content.replace("{{EDGES_COUNT}}", str(len(edges_list)))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Сохранён HTML: {output_file}")

# ----------------------------------------------------------------------
#  Экспорт в DOT и PNG (опционально)
# ----------------------------------------------------------------------

def export_dot(nodes: Dict[str, dict], edges: List[tuple], dot_file: str):
    """Сохраняет граф в формате DOT."""
    with open(dot_file, 'w', encoding='utf-8') as f:
        f.write("digraph GitGraph {\n")
        f.write("  rankdir=TB;\n")
        f.write("  node [style=filled];\n")
        for node_id, attrs in nodes.items():
            shape_map = {"ellipse": "circle", "box": "box", "diamond": "diamond", "star": "star"}
            shape = shape_map.get(attrs.get("shape", "ellipse"), "ellipse")
            label = attrs.get("label", node_id)
            color = attrs.get("color", {}).get("background", "lightgray")
            f.write(f'  "{node_id}" [label="{label}", shape={shape}, fillcolor="{color}"];\n')
        for u, v in edges:
            f.write(f'  "{u}" -> "{v}";\n')
        f.write("}\n")
    print(f"Сохранён DOT: {dot_file}")

def render_png(dot_file: str, png_file: str):
    """Конвертирует DOT в PNG через Graphviz (требуется dot в PATH)."""
    try:
        subprocess.run(['dot', '-Tpng', dot_file, '-o', png_file], check=True)
        print(f"Сохранён PNG: {png_file}")
    except Exception as e:
        print(f"Не удалось создать PNG (Graphviz не установлен или не в PATH): {e}")

# ----------------------------------------------------------------------
#  Основная функция
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Ультимативная визуализация Git")
    parser.add_argument('--full', action='store_true', help='Не сворачивать линейные цепочки')
    parser.add_argument('--dot', action='store_true', help='Дополнительно экспортировать DOT и PNG')
    parser.add_argument('--output', default='git_viz.html', help='Имя выходного HTML-файла')
    args = parser.parse_args()

    if not os.path.isdir('.git'):
        print("Ошибка: не найден каталог .git. Запустите скрипт в корне Git-репозитория.")
        sys.exit(1)

    print("Загрузка коммитов...")
    commits = get_all_commits()
    if not commits:
        print("Нет коммитов или ошибка доступа к репозиторию.")
        return

    if not args.full:
        print("Вычисление цепочек для сворачивания...")
        mapping = compute_linear_chains(commits)
    else:
        mapping = {h: h for h in commits}

    print("Построение узлов и рёбер...")
    nodes, edges = collapse_commits(commits, mapping)

    print("Добавление тегов и веток...")
    tags = get_all_tags()
    branches = get_branches()
    head = get_head()
    nodes, edges = add_tags_and_branches(nodes, edges, tags, branches, head)

    print(f"Итоговый граф: {len(nodes)} узлов, {len(edges)} рёбер")

    print("Генерация HTML...")
    generate_html(nodes, edges, args.output)

    if args.dot:
        dot_file = args.output.replace('.html', '.dot')
        export_dot(nodes, edges, dot_file)
        render_png(dot_file, dot_file.replace('.dot', '.png'))

    print(f"Готово! Откройте {args.output} в браузере.")

if __name__ == "__main__":
    main()