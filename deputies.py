#!/usr/bin/env python3
import csv
import argparse
import networkx as nx
# Use PyVis for interactive visualization
try:
    from pyvis.network import Network
except ImportError:
    raise ImportError("Please install pyvis: pip install pyvis")

def read_rows(csv_path):
    """Yield rows as dicts with expected keys."""
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required = {'candidate_surname','candidate_firstname','proposer','seconder'}
        if not required.issubset(reader.fieldnames or []):
            missing = required - set(reader.fieldnames or [])
            raise ValueError(f"CSV missing columns: {missing}")
        for row in reader:
            yield row


def build_graph(rows):
    G = nx.DiGraph()
    for row in rows:
        cand = f"{row['candidate_firstname']} {row['candidate_surname']}"
        G.add_node(cand, role='candidate')
        for role in ['proposer','seconder']:
            nom = row[role].strip()
            if nom:
                G.add_node(nom, role=role)
                G.add_edge(nom, cand, relation=role)
    return G


def export_html(G, output_path, height='750px', width='100%'):
    """
    Export the graph `G` to an interactive HTML using PyVis.
    """
    net = Network(height=height, width=width, directed=True, notebook=False)
    # Optional: configure physics controls via UI
    net.show_buttons(filter_=['physics'])

    # Add nodes with group attribute for coloring
    for n, attr in G.nodes(data=True):
        group = attr.get('role', 'other')
        net.add_node(n, label=n, title=group, group=group)

    # Add edges
    for src, dst, attr in G.edges(data=True):
        title = attr.get('relation', '')
        net.add_edge(src, dst, title=title, arrowStrikethrough=False)

    # Write HTML directly instead of show() to avoid template issues
    net.write_html(output_path)
    print(f"Interactive HTML saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate an interactive nomination network HTML.")
    parser.add_argument('-i','--input',  required=True, help="CSV file path")
    parser.add_argument('-o','--output', default='nominations_network.html', help="Output HTML file")
    args = parser.parse_args()

    rows = list(read_rows(args.input))
    G = build_graph(rows)
    export_html(G, args.output)

if __name__ == '__main__':
    main()
