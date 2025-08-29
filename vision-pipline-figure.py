from graphviz import Digraph

# Create a directed graph
dot = Digraph(comment="Computer Vision Pipeline: Real vs Synthetic (GTA5) Data Models")

dot.attr(rankdir='TB', size='8')

# Nodes
dot.node('A', 'Real Data', shape='box', style='filled', fillcolor='lightblue')
dot.node('B', 'Synthetic Data (PreSIL - GTA5)', shape='box', style='filled', fillcolor='lightblue')

dot.node('C', 'R1: Synthetic-only (PreSIL)', shape='box', style='filled', fillcolor='lightcyan')
dot.node('D', 'R2: Real-only (KITTI)', shape='box', style='filled', fillcolor='lightcyan')
dot.node('E', 'R3: Synthetic-heavy mix\n(90% PreSIL + 10% Cityscapes)', shape='box', style='filled', fillcolor='lightcyan')

dot.node('F', 'Models:\nRT-DETR, YOLOv10', shape='box', style='filled', fillcolor='lightyellow')
dot.node('G', 'Evaluation:\nmAP50, mAP50–95,\nclass-wise (car, person)', shape='box', style='filled', fillcolor='lightgrey')

# Edges
dot.edge('A', 'C')
dot.edge('A', 'D')
dot.edge('B', 'C')
dot.edge('B', 'E')
dot.edge('A', 'E')
dot.edge('C', 'F')
dot.edge('D', 'F')
dot.edge('E', 'F')
dot.edge('F', 'G')

# Render as PNG
output_path = '/mnt/data/computer_vision_pipeline_en'
dot.render(output_path, format='png', cleanup=True)

output_path + ".png"
