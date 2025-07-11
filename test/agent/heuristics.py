from graphviz import Digraph

color_map = {
    "white": "#FFFFFF",
    'light_blue': '#AED6F1',
    'light_green': '#A9DFBF',
    'light_yellow': '#F9E79F',
    'light_red': '#F5B7B1'
}

dot = Digraph(comment='Energy Management Decision Tree')
dot.attr(margin="0", pad="0.1")  # Tight layout
dot.attr('node', shape='box', style='rounded,filled', color='black', fontname='Helvetica')

dot.node('A', 'load - pv < 0?', fillcolor=color_map['white'])
dot.node('B', 'soc < 1.0 AND capa_to_charge > 0?', fillcolor=color_map['white'])
dot.node('C', 'Charge battery (0)', fillcolor=color_map['light_blue'])
dot.node('D', 'Export excess (3)', fillcolor=color_map['light_green'])
dot.node('E', 'soc > 0.0 AND capa_to_discharge > 0?', fillcolor=color_map['white'])
dot.node('F', 'Discharge battery (1)', fillcolor=color_map['light_yellow'])
dot.node('G', 'Grid import (2)', fillcolor=color_map['light_red'])
# dot.node('H', 'Fallback: Grid import (2)', fillcolor=color_map['light_red'])

dot.edge('A', 'B', 'Yes')
dot.edge('B', 'C', 'Yes')
dot.edge('B', 'D', 'No')
dot.edge('A', 'E', 'No')
dot.edge('E', 'F', 'Yes')
dot.edge('E', 'G', 'No')
# dot.edge('A', 'H', 'Fallback', style='dashed')

dot.render('heuristics_decision_tree', format='pdf', cleanup=True)
dot.render('heuristics_decision_tree', format='png', cleanup=True)
