import sys
import numpy as np
from igraph import *

class DynamicManufacturing:

	def __init__(self, network, seed):
		# Parameters
		# network: igraph.Graph

		self.network = network
		self.time = 0

		self.buffer = np.array([0.0 for i in range(network.vcount())])
		self.state = np.array(["starved" for i in range(network.vcount())])
		self.state_id = np.array([0 for i in range(network.vcount())]) 
		# 0 -> starved / 1 -> blocked / 2 -> working

		# random number generator
		# the numbers generated are smaller than 1
		self.rng = np.random.default_rng(seed=seed)

	def iterate(self, output):
		# output is a file to output data from the simulation

		# initialize production
		total_production = 0

		# write the header to the file
		if self.time == 0:
			output.write("time,vertex,state,state_id,buffer,production_step\n")

		# increase time
		self.time = self.time + 1

		ids = self.network.vs["label"]
		prate = np.array(self.network.vs["production_rate"])
		frate = np.array(self.network.vs["failure_rate"])
		buffer_size = np.array(self.network.vs["buffer_size"])
		production_step = np.array(self.network.vs["production_step"])

		# loop through the nodes in the network sorted in
		# topological order
		for i in self.network.topological_sorting():
			# calculate the in and out edges of node i
			# and make a list of in and out nodes linked to the node
			in_nodes = [self.network.get_edgelist()[edge.index][0] for edge in self.network.vs[i].in_edges()]
			out_nodes = [self.network.get_edgelist()[edge.index][1] for edge in self.network.vs[i].out_edges()]

			# check if any of the elements feeded by node i has space to receive
			# materials. If any node has possibility to recceive materials, node i
			# can produce them.
			if len(out_nodes) > 0 and np.all(self.buffer[out_nodes] >= buffer_size[out_nodes]):
				# if all nodes receiving from i are full, i is blocked
				self.state[i] = "blocked"
				self.state_id[i] = 1
				# 0 -> starved / 1 -> blocked / 2 -> working

			# if it is a node in the first production step, it is not starved
			elif len(in_nodes) == 0:
				self.state[i] = "working"
				self.state_id[i] = 2
				# 0 -> starved / 1 -> blocked / 2 -> working

			# if it does not have any raw materials, it is starved
			elif self.buffer[i] == 0:
				self.state[i] = "starved"
				self.state_id[i] = 0
				# 0 -> starved / 1 -> blocked / 2 -> working

			else:
				self.state[i] = "working"
				self.state_id[i] = 2
				# 0 -> starved / 1 -> blocked / 2 -> working

			# check if the machine is working and does not experience failure
			if self.state[i] == "working" and self.rng.random() > frate[i]:

				# calculate production
				production = prate[i]

				# if it has incoming edges, it can make the production rate
				# only if it has enough material on its buffer
				if len(in_nodes) > 0:
					production = min(production, self.buffer[i])

				# its production can be at maximum the amount available in the
				# buffers of the nodes ahead
				if len(out_nodes) > 0:
					production = min(production, np.max(buffer_size[out_nodes]-self.buffer[out_nodes]))

				# produce!
				# decrease its own buffer by the amount of product it make
				if len(in_nodes) > 0:
					self.buffer[i] = self.buffer[i] - production

				# increase the amount of product in the buffer of the node it is providing
				if len(out_nodes) > 0:
					# find the out_node with minimum occupation on its buffer
					index = np.argmin(self.buffer[out_nodes])
					node_to_feed = out_nodes[index]
					self.buffer[node_to_feed] = np.minimum(buffer_size[node_to_feed], self.buffer[node_to_feed]+production)
				# if the node does not have outgoing edges, the production is
				# the production of the whole process
				else:
					total_production = total_production + production
					print("[INFO] production: {}".format(total_production))

			# write status to file
			output.write("{},{},{},{},{},{}\n".format(self.time, ids[i], self.state[i], self.state_id[i], self.buffer[i], production_step[i]))

		return total_production



