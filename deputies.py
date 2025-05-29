#!/usr/bin/env python3
import csv
import argparse
import networkx as nx
import os
# Use PyVis for interactive visualization
try:
    from pyvis.network import Network
except ImportError:
    raise ImportError("Please install pyvis: pip install pyvis")

# Define custom colors for each role
ROLE_COLORS = {
    'candidate': {'background': '#e41a1c', 'border': '#a50f15'},  # red
    'proposer':  {'background': '#ffff33', 'border': '#cccc29'},  # yellow
    'seconder':  {'background': '#377eb8', 'border': '#265a88'},  # blue
}

def read_rows(csv_path):
    """Read CSV into a list of dicts with required columns."""
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required = {'candidate_surname', 'candidate_firstname', 'proposer', 'seconder'}
        if not required.issubset(reader.fieldnames or []):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"CSV missing columns: {missing}")
        return list(reader)


def build_graph(rows):
    """Construct directed graph, marking all candidates distinctly."""
    G = nx.DiGraph()
    # Add all candidates first
    for row in rows:
        cand = f"{row['candidate_firstname']} {row['candidate_surname']}"
        G.add_node(cand, role='candidate')
    # Add proposers/seconders and edges
    for row in rows:
        cand = f"{row['candidate_firstname']} {row['candidate_surname']}"
        for relation in ('proposer', 'seconder'):
            nom = row[relation].strip()
            if nom:
                if not G.has_node(nom):
                    G.add_node(nom, role=relation)
                G.add_edge(nom, cand, relation=relation)
    return G


def export_html(G, output_path, height='750px', width='100%'):
    """Export the graph to interactive HTML with search and double-click search."""
    net = Network(height=height, width=width, directed=True, notebook=False)
    net.show_buttons(filter_=['physics'])

    # Add nodes with custom colors
    for node, attr in G.nodes(data=True):
        role = attr.get('role', 'other')
        color = ROLE_COLORS.get(role, {'background':'#999999','border':'#666666'})
        net.add_node(
            node,
            label=node,
            title=role.capitalize(),
            color={
                'background': color['background'],
                'border': color['border'],
                'highlight': {'background': color['border'], 'border': color['background']}
            }
        )

    # Add edges
    for src, dst, attr in G.edges(data=True):
        net.add_edge(src, dst, title=attr.get('relation', ''), arrowStrikethrough=False)

    # Write default HTML to a valid temp file
    tmp_html = output_path + '.tmp.html'
    net.write_html(tmp_html)

    # Inject search box and robust double-click search script into HTML
    injection = '''
<div style="padding:10px; background:#f9f9f9; border-bottom:1px solid #ddd;">
  <input id="node-search" type="text" placeholder="Search node..." style="width:200px;" />
  <button onclick="searchNode()">Search</button>
</div>
<script type="text/javascript">
  document.addEventListener("DOMContentLoaded", function() {
    // search function
    window.searchNode = function() {
      var term = document.getElementById('node-search').value.toLowerCase();
      if (!term) return;
      var all = network.body.data.nodes.get();
      var matches = all.filter(n => n.label.toLowerCase().includes(term)).map(n => n.id);
      network.selectNodes(matches);
      if (matches.length) network.focus(matches[0], {scale:1.5});
    };
    // double-click search on node
    network.on('doubleClick', function(params) {
      if (params.nodes && params.nodes.length) {
        var node = network.body.data.nodes.get(params.nodes[0]);
        var query = encodeURIComponent(node.label);
        window.open('https://www.google.com/search?q=' + query, '_blank');
      }
    });
  });
</script>
'''
    with open(tmp_html, 'r', encoding='utf-8') as f:
        html = f.read()
    html = html.replace('<body>', '<body>' + injection)
    # Write final HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    os.remove(tmp_html)
    print(f"Interactive HTML with search saved to: {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate an interactive nomination network HTML with search.")
    parser.add_argument('-i', '--input', required=True, help="CSV file path")
    parser.add_argument('-o', '--output', default='nominations_network.html', help="Output HTML file")
    args = parser.parse_args()
    rows = read_rows(args.input)
    G = build_graph(rows)
    export_html(G, args.output)
