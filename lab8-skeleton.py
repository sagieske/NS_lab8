# Netwerken en Systeembeveiliging
# Lab 8 - Distributed Sensor Network
# Author(s) and student ID(s):
# Group: Eszter Fodor (5873320) & Sharon Gieske (6167667), group 15
# Date: 10-12-2012
import sys
import struct
import random
import time
import math
from gui import MainWindow
from sensor import *
from socket import *

########### Task 1 #############
def setup_globals():
	# Create global variable
	# Global lists
	global neighbors, received_reply
	neighbors = []				# List of all known neighbors 
	received_reply = []			# List to keep track of received echo_reply

	# Global counters
	global reply_counter, sequenceNode
	reply_counter = 0			# Counter for replies received from neighbors\
	sequenceNode = 0

	# Global misc
	global unknown, sensorvalue, portnumber
	sensorvalue = random.randint(0, 10000)
	unknown = (-1,-1)			# Used when location is unknown (father) or unnecessary (neighbors) in message\
	global last_wave	
	last_wave = (-1,-1)			# Last wave received.  TODO: is this a list of all waves? Or just last wave?


def send_ping(peer):
	"""
	Send mulitcast ping
	"""
	#1.1: Send multicast PING with initiators location 
	#Seq number set to 0 with ping, neighbor is unknown so is set to -1,-1 since this is off the grid)
	ping_enc_sent = message_encode(MSG_PING, 0, node_location, (-1,-1))
	peer.sendto(ping_enc_sent, (MCAST_GRP, MCAST_PORT))
	print "SEND_PING ready"

def send_pong(peer, initiator, address):
	"""
	Send mulitcast ping
	"""
	pong_location = node_location
	pong_enc_sent = message_encode(MSG_PONG, 0, initiator, pong_location)
	peer.sendto(pong_enc_sent, address)


def move():
	"""
	Creates random position for node in 100 x 100 grid
	"""
	global nx, ny,  node_location
	nx = random.randint(0, GRID_SIZE)
	ny = random.randint(0, GRID_SIZE)
	node_location = (nx,ny)
	return node_location

def list(window):
	"""
	List all new neighbors responded to ping
	"""
	window.writeln("Neighbor INFORMATION:")
	index = 1
	for i in neighbors:
		location, port = i
		window.writeln(str(index) + ". Position:\t" + str(location) +  ", IP:port :\t" + str(port))
		index += 1


########### Task 2 #############

# FOR FIRST ECHO (Task 2.1)
def send_echo(peer,window, father = (-1,-1), seqnumber = 0):
	"""
	Send echo to all neighbors
	"""

	# Only 1 neighbor and already known father, send echo reply
	# TODO: add wave to received to last_wave
	if(len(neighbors) == 1 and father != (-1,-1)):
		# Get address for ECHO Reply
		location, address = neighbors[0]
		# Encode message. Neighbor location not needed -> -1, -1 not possible for grid location
		pong_enc_sent = message_encode(MSG_ECHO_REPLY,  seqnumber, father, (-1,-1), OP_NOOP)
		peer.sendto(pong_enc_sent, address)
		window.writeln("Echo sent echo reply to : " + str(father) + "\tSequence: " + str(seqnumber))	

	# Multiple neighbors, send new wave
	else:
		#new_sequence = seqnumber + 1
		# Encode message. Neighbor location not needed -> -1, -1 not possible for grid location
		pong_enc_sent = message_encode(MSG_ECHO,  seqnumber, node_location, (-1,-1), OP_NOOP)

		# Sent to all neighbors
		for i in neighbors:
			location, address = i
			# If known father, do not send back to father
			if(father == location):
				pass
			else:
				peer.sendto(pong_enc_sent, address)

		# Debug line
		window.writeln("Echo sent with init from: " + str(node_location) + "\tSequence: " + str(seqnumber))	


# 2.4
"""
When a non-initiator receives an ECHO from the same wave again, send an ECHO_REPLY to sender.

def receive_wave(peer, window, message_dec_recv):
	type, sequence, initiator, neighbor_pos, _, _ = message_dec_recv	
	# Echo has been received previously
	if((-1,1) == (sequence, initiator)):
		pong_enc_sent = message_encode(MSG_ECHO_REPLY, sequence, initiator, neighbor_pos, OP_NOOP, 0)
		window.writeln("ECHO DUBBLE") 		
	# Add wave to received
	window.writeln("TESTING - receive wave")
"""
# 2.5
"""
When non-initiator recieved ECHO_REPLY from all neighbours, send ECHO_REPLY to father.
"""

def process_echo_reply(peer, window, message, address):
	"""
	Process an echo reply
	"""	
	reply_counter = 0
	print "1: ",reply_counter
	type, sequence, initiator, neighbor_pos, operation, payload = message	
	# Increment reply counter	
	reply_counter += 1
	print "2: ", reply_counter
	
	# Reply from all neighbors
	if(len(neighbors) == reply_counter):
		#global reply_counter
		#reply_counter = 0
		# Node was initiator
		if(initiator == node_location):
			window.writeln("Decide!")
		# Send echo reply to father		
		else:
			# Encode message
			echorep_enc_sent = message_encode(MSG_ECHO_REPLY,  sequence, initiator, neighbor_pos, operation, payload)
			# Send echo reply to father			
			peer.sendto(echorep_enc_sent, address)

"""
#TODO: WORK IN PROGRESS
def process_echo(peer, window, message, address):
	type, sequence, initiator, neighbor_pos, operation, payload = message
	wave = (sequence, initiator)

	# Wave is previously received or only one neighbor
	if( wave == last_wave or len(neighbors) == 1):
		if (wave == last_wave):
			window.writeln("Double wave")
		else:
			window.writeln("Only 1 neighbor")
		# Encode message
		echorep_enc_sent = message_encode(MSG_ECHO_REPLY,  sequence, initiator, neighbor_pos, operation, payload)
		# Send echo reply			
		peer.sendto(echorep_enc_sent, address)
		# SEND ECHO TO NEIGHBORS.
		pass
"""

"""
process echo:
	IF only one neighbour OR already received wave:
		send ECHO_REPLY
	ELIF more neighbors:
		send ECHO with sequence+1
"""

def process_echo_retry(peer, window, message, address):
	type, sequence, initiator, neighbor_pos, operation, payload = message
	wave = (sequence, initiator)
	
	# If already received or only 1 neigbor
	if((wave in last_wave) or len(neighbors) == 1):
		if((wave in last_wave)):
			window.writeln("Double wave")
		else:
			window.writeln("Only 1 neighbor")
		# Encode message
		echorep_enc_sent = message_encode(MSG_ECHO_REPLY,  sequence, initiator, neighbor_pos, operation, payload)
		# Send echo reply to sender		
		peer.sendto(echorep_enc_sent, address)
	elif(len(neighbors) > 1):
		sequence = sequence + 1
		# Encode message. Neighbor location not needed -> -1, -1 not possible for grid location
		pong_enc_sent = message_encode(MSG_ECHO,  sequence, node_location, (-1,-1), OP_NOOP)

		# Send to all neighbors
		for i in neighbors:
			location, address = i
			# If known father, do not send back to father
			if(initiator == location):
				pass
			else:
				peer.sendto(pong_enc_sent, address)

		# Debug line
		window.writeln("Echo sent with init from: " + str(node_location) + "\tSequence: " + str(sequence))	
	else:
		print "Something went wrong..."



def check_multicast(mcast, peer):
	"""
	Check for receiving ping messages on multicast listener socket
	"""
	try:
		ping_enc_recv, address_mcast = mcast.recvfrom(10240)
		ip_ping, port_ping = address_mcast
		
		# Decode message
		ping_dec_recv = message_decode(ping_enc_recv)
		type, _, initiator, _, _, _ = ping_dec_recv	# only PING can be sent on mcast
		ix, iy = initiator
		
		#calculate range with pythagoras
		distance = math.pow(abs(ny-iy), 2) + math.pow(abs(nx-ix),2)

		# Ping is sent by same node		
		if(port_ping == portnumber):
			pass	
		# Initiator is not in same range
		elif( distance > math.pow(SENSOR_RANGE,2)):
			pass
		# Initiator is in same range
		else:
			send_pong(peer, initiator, address_mcast)

	except error:
		pass
	
def check_socket_recv(peer, window):
	"""
	Check for receiving pong/echo/echo_reply messages
	"""

	# Check for receiving messages on peer socket
	try:
		message_enc_recv, address = peer.recvfrom(10240)

		# Decode message
		message_dec_recv = message_decode(message_enc_recv)
		type, sequence, initiator, neighbor_pos, _, _ = message_dec_recv	
		
		# Check type of message
		if(type == 1):			# Receiving PONG message
			window.writeln("PONG")			
			# Add neighbor if not already in list
			neighbor = (neighbor_pos, address)
			if neighbor not in neighbors:
				neighbors.append(neighbor)
			
		elif(type == 2): 	# Receiving ECHO message
			window.writeln("Received ECHO wave: " + str(initiator) + "\tSequence: " + str(sequence))	
			#receive_wave(peer, window, message_dec_recv)				
			#send_echo(peer, window, initiator, sequence)			
			process_echo_retry(peer, window, message_dec_recv, address)

		elif(type == 3):		# Receiving ECHO REPLY message
			window.writeln("Received ECHO REPLY to wave: " + str(initiator) + "\tSequence: " + str(sequence))	
			process_echo_reply(peer, window, message_dec_recv, address)
	except error:
		pass

def socket_subscribe_mcast(sock, ip):
	"""
	Subscribes a socket to multicast.
	"""
	mreq = struct.pack("4sl", inet_aton(ip), INADDR_ANY)
	sock.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
		
def main(argv):
	"""
	Program entry point.
	"""
	## Create the multicast listener socket and suscribe to multicast.
	mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
	socket_subscribe_mcast(mcast, MCAST_GRP)
	# Set socket as reusable.
	mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	# Bind it to the multicast address.
	# NOTE: You may have to bind to localhost or '' instead of MCAST_GRP
	# depending on your operating system.
	# ALSO: In the lab room change the port to MCAST_PORT + group number
	# so that messages from different groups do not interfere.
	# When you hand in your code in it must listen on (MCAST_GRP, MCAST_PORT).
	mcast.bind((MCAST_GRP, MCAST_PORT))

	## Create the peer-to-peer socket.
	peer = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
	# Set the socket multicast TTL so it can send multicast messages.
	peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 2)
	# Bind the socket to a random port.
	peer.bind(('', INADDR_ANY))

	## This is the event loop.
	window = MainWindow()

#---------- BEGIN EIGEN CODE ------------#
	
	# Set up most of the globals
	setup_globals()

	global portnumber
	# Get socket information
	_, portnumber = peer.getsockname()
	
	global a, b
	a = 1
	b = 2

	# Set blocking to zero
	peer.setblocking(0)
	mcast.setblocking(0)

	# Set up position node
	move()

	# Print out information in gui
	window.write("INFORMATION\nIP:port:\t" + str(portnumber) + "\nPosition:\t" + str(node_location) + "\nSensor Value:\t" + str(sensorvalue) + "\n")

	# Send multicast PING
	send_ping(peer)
	
	# Set time	
	pingtime = time.time()

	while window.update():
		# Resend PING if time > 5s, reset
		if(time.time() - PING_PERIOD > pingtime):
			del neighbors[:] # Empty neighbors list
			send_ping(peer)
			pingtime = time.time()
			#window.writeln("------------------ reset ---------------------")
		
		# Check for receiving on multicast	
		check_multicast(mcast,peer)

		# Check for receiving on peer
		check_socket_recv(peer, window)

		# Get commands input
		command = window.getline()
		if (command == "ping"):
			window.writeln("> Command entered: " + command)
			window.writeln("Sending ping over multicast...")
			send_ping(peer)

		elif (command == "list"):
			window.writeln("> Command entered: " + command)
			list(window)

		elif (command == "move"):
			window.writeln("> Command entered: " + command)
			new_location = move()
			window.writeln("New location:" + str(new_location))

		elif (command == "echo"):
			window.writeln("> Command entered: " + command)
			send_echo(peer, window)

		elif (command == ""):
			pass

		else:
			window.writeln("The command \'" + str(command) + "\' is unknown.")



if __name__ == '__main__':
	sys.exit(main(sys.argv))
