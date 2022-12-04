from anytree import Node
root = Node("root")
s0 = Node("sub0", parent=root, edge=2)
s0b = Node("sub0B", parent=s0, foo=4, edge=109)
s0a = Node("sub0A", parent=s0, edge="")
s1 = Node("sub1", parent=root, edge="")
s1a = Node("sub1A", parent=s1, edge=7)
s1b = Node("sub1B", parent=s1, edge=8)
s1c = Node("sub1C", parent=s1, edge=22)
s1ca = Node("sub1Ca", parent=s1c, edge=42)
from anytree.exporter import DotExporter
for line in DotExporter(root):
     print(line)
