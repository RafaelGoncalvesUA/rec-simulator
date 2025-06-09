import graphviz

dot = """
digraph Tree {
node [shape=box, style="filled, rounded", color="black", fontname=helvetica] ;
edge [fontname=helvetica] ;

0 [label="hour_sin <= -0.604\\nclass = full discharge", fillcolor="#c4f3d5"];
1 [label="yhat1 <= 74.524\\nclass = import", fillcolor="#e6fce9"];
2 [label="pv <= 0.607\\nclass = import", fillcolor="#62e688"];
3 [label="...", fillcolor="#dddddd"];
4 [label="...", fillcolor="#dddddd"];
5 [label="grid_price_import <= 0.486\\nclass = full discharge", fillcolor="#a0f3b7"];
6 [label="...", fillcolor="#dddddd"];
7 [label="...", fillcolor="#dddddd"];
8 [label="hour_sin <= -0.129\\nclass = full discharge", fillcolor="#4ce96f"];
9 [label="yhat1 <= 71.485\\nclass = full discharge", fillcolor="#79eca0"];
10 [label="...", fillcolor="#dddddd"];
11 [label="...", fillcolor="#dddddd"];
12 [label="battery_soc <= 0.319\\nclass = full discharge", fillcolor="#41e564"];
13 [label="...", fillcolor="#dddddd"];
14 [label="...", fillcolor="#dddddd"];

0 -> 1 [label="True"];
0 -> 8 [label="False"];
1 -> 2 [label="True"];
1 -> 5 [label="False"];
2 -> 3 [label="True"];
2 -> 4 [label="False"];
5 -> 6 [label="True"];
5 -> 7 [label="False"];
8 -> 9 [label="True"];
8 -> 12 [label="False"];
9 -> 10 [label="True"];
9 -> 11 [label="False"];
12 -> 13 [label="True"];
12 -> 14 [label="False"];
}
"""

graph = graphviz.Source(dot)
graph.render("decision_tree", format="pdf", cleanup=True)
