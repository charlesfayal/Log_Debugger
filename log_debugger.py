from difflib import SequenceMatcher

import csv
import re
import graphviz as gv 
from string import digits

SIMILARITY_THRESHOLD = 0.4 

START_LINE = "begin level control 1 replan"
#file_name = "test_log.txt"
file_name = 'test-logs/LevelControl1.txt'
regex = '[0-9]*-[0-9]*-[0-9]* [0-9]*:[0-9]*:[0-9]*,[0-9]* \[(.*)\] (\S*)[\s-]*(.*)'
connecting_lines = ['next task plans', 'end level control  replan. computation time =  msec PlanResult=NoError errorCounter= noActionCounter='] #lines that are unique commonly used 

class ID_Counter():
	def __init__(self):
		self.id_count = 0

	def get_next(self):
		self.id_count += 1
		return self.id_count 

def similar(a, b):
    return SequenceMatcher(None, a.strip(), b.strip()).ratio()

def similar_enough(a,b):
	similarity = similar(a,b)
	if similarity > 0.6:
		return True
	return False

def add_nodes(current_node, graph):
	for next_node in current_node.next_nodes:
		graph.node(next_node.line,next_node.line)
		graph.edge(current_node.line,next_node.line, constraint='true')
		add_nodes(next_node,graph)

def add_nodes_from_dic(dic, graph):
	for node in dic:
		graph.node(node,node) # doens't have all nodes necessarily
		next_nodes = dic[node]
		for next_node in next_nodes:
			count = next_nodes[next_node]
			color = 'black'
			if count == 1:
				color = 'red'
			graph.edge(node,next_node, label=str(count), color=color)


def build_edge_dic(current_node, edges, nodes):
	edge_dic = {}
	if current_node.id in nodes:
		#already searched
		return

	nodes[current_node.id] = current_node.line
	if current_node.id not in edges:
		edges[current_node.id] = edge_dic
	else:
		edge_dic = edges[current_node.id]

	for next_node in current_node.next_nodes:
		if next_node.id not in edge_dic:
			edge_dic[next_node.id] = current_node.next_nodes[next_node]
		else:
			edge_dic[next_node.id] = edge_dic[next_node.id] + 1
		if next_node != current_node:
			build_edge_dic(next_node,edges,nodes)

def create_graph(start_node):
	print("Creating graph")

	dot = gv.Digraph(comment='Log Graph')
	#dot.node(start_node.line,start_node.line)
	#add_nodes(start_node,dot)
	edges = {}
	nodes = {}
	build_edge_dic(start_node,edges, nodes)
	print("Edges:")
	print(edges)

	with open('node_to_line.csv', 'wb') as csv_file:
	    writer = csv.writer(csv_file)
	    for key, value in nodes.items():
	       writer.writerow([key, value])

	add_nodes_from_dic(edges,dot)

	dot.render('test-output/round-table.gv', view=True)  

class Node():
	def __init__(self,line,id_counter, parent):
		self.line = line.strip()
		self.next_nodes = {} # next node to count
		self.id = str(id_counter.get_next())
		self.parent = parent

	# Finds the next node from the current node, or creates a new one
	def next_node(self,input_line,id_counter):
		next_node = self.search_for_node(input_line)
		if not next_node:
			next_node = Node(input_line, id_counter, self)

		self.add_next_node(next_node)

		return next_node

	def search_this_node_and_children(self,input_line):
		if similar_enough(input_line,self.line):
			return self

		for node in self.next_nodes:
			if similar_enough(input_line,node.line):
				return node
			for next_node in node.next_nodes:
				if similar_enough(input_line, next_node.line):
					return next_node

	def add_next_node(self,next_node):
		if next_node not in self.next_nodes:
			self.next_nodes[next_node] = 0

		self.next_nodes[next_node] = self.next_nodes[next_node] + 1

	def search_for_node(self, input_line):
		node = self.search_this_node_and_children(input_line)
		if node:
			return node

		#go back up the tree and check the parents children
		parent = self.parent
		for i in range(10):
			if parent:
				node = parent.search_this_node_and_children(input_line) # redundantly checks self 
				if node:
					return node
				parent = parent.parent


		return None

	def __str__(self):
		return "[" + self.line + "]" + "[ next_nodes= " + str(len(self.next_nodes)) + "]"	

def main():
	id_counter = ID_Counter()
	log = open(file_name, "r")
	start_node = Node(START_LINE,id_counter, None)
	node = start_node
	current_thread = 0
	connecting_nodes = {}
	for line in connecting_lines:
		connecting_nodes[line] = Node(line,id_counter,None)

	for line in log.readlines():
		m = re.search(regex,line)
		if m is not None:
			#print(m.group(3))
			thread = m.group(1)
			log_type = m.group(2)
			parsed_line = m.group(3).strip()

			parsed_letters = parsed_line.translate(None, digits)
			if not parsed_line:
				# Skip empty lines
				continue

			if similar_enough(parsed_letters,START_LINE):
				node = start_node
				current_thread = thread
				continue

			if thread != current_thread:
				#different thread don't care about it
				continue

			for connect_node_line in connecting_nodes:
				if not similar_enough(connect_node_line, parsed_line):
					continue

				connect_node = connecting_nodes[connect_node_line]
				if not connect_node.parent:
					connect_node.parent = node
				node.add_next_node(connect_node)

				node = connect_node

			node = node.next_node(parsed_letters, id_counter)
			#print(node)
		# else:
		# 	print("Could not parse")
		# 	print(line)

	log.close()
	create_graph(start_node)



if __name__ == "__main__":
	main()