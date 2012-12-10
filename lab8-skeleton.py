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

network_size = 0

########### Task 1 #############
def setup_globals():
	# Create global variable
	# Global lists
	global neighbors, received_reply
	neighbors = []				# List of all known neighbors 
	received_reply = []			# List to keep track of received echo_reply

	# Global counters
	global sequencenumber, echo_reply_counter, payload_counter
	sequencenumber = 0
	echo_reply_counter = 0 # Counter for replies received from neighbors
	payload_counter = 0

	# Global misc
	global unknown, sensorvalue, portnumber, father
	sensorvalue = random.randint(0, 10000)
	unknown = (-1,-1)			# Used when location is unknown (father) or unnecessary (neighbors) in message
	global last_wave	
	last_wave = (-1,-1)			# Last wave received.  TODO: is this a list of all waves? Or just last wave?

def give_info(window):
	# Print out information in gui
	global portnumber, node_location, sensor_value
	window.write("INFORMATION\nIP:port:\t\t" + str(portnumber) + "\nPosition:\t\t" + str(node_location) + "\nSensor Value:\t\t" + str(sensorvalue) + "\n")

def send_ping(peer):
	"""
	Send mulitcast ping
	"""
	#1.1: Send multicast PING with initiators location 
	#Seq number set to 0 with ping, neighbor is unknown so is set to -1,-1 since this is off the grid)
	ping_enc_sent = message_encode(MSG_PING, 0, node_location, (-1,-1))
	peer.sendto(ping_enc_sent, (MCAST_GRP, MCAST_PORT))

def send_pong(peer, initiator, address):
	"""
	Send pong
	"""
	pong_location = node_location
	pong_enc_sent = message_encode(MSG_PONG, 0, initiator, pong_location)
	peer.sendto(pong_enc_sent, address)

#TODO: Changed for testing
def move(inputx = -1, inputy = -1):
	"""
	Creates random position for node in grid of GRIDSIZE x GRIDSIZE
	"""
	#TODO: Remove if else for submission!
	global nx, ny,  node_location
	if(inputx == -1 and inputy == -1):
		nx = random.randint(0, GRID_SIZE)
		ny = random.randint(0, GRID_SIZE)
	else:
		nx = inputx
		ny = inputy
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

def send_echo(peer,window):
	"""
	Initiate echo wave to neighbors
	"""
	# create echo message
	global sequencenumber
	pong_enc_sent = message_encode(MSG_ECHO,  sequencenumber, node_location, (-1,-1), OP_NOOP, 0)

	# Sent to all neighbors
	for i in neighbors:
		location, address = i
		peer.sendto(pong_enc_sent, address)

	window.writeln("-> message sent: (MSG_ECHO_REPLY," + str(sequencenumber) + "," + str(node_location) + ",(-1,-1),"+ " OP_NOOP, 0)")


	# Increment sequencenumber
	sequencenumber += 1

def send_wave_further(peer,window, message, father):
	"""
	Send wave further to the rest of neighbors
	"""
	global echo_reply_counter
	echo_reply_counter += 1

	# Send wave to all neighbors
	for i in neighbors:
		location, address = i
		# Do not send wave to father
		if(address == father):
			pass
		else: 
			pong_enc_sent = message_encode(MSG_ECHO,  message[1], message[2], message[3], message[4], message[5])
			peer.sendto(pong_enc_sent, address)

def send_echo_reply(peer,window, message, address):
	"""
	Send reply to sender
	"""
	pong_enc_sent = message_encode(MSG_ECHO_REPLY,  message[1], message[2], message[3], message[4], message[5])
	peer.sendto(pong_enc_sent, address)
	window.writeln("[S] Echo reply sent to " + str(father)) 

def process_echo(peer, window, message, address):
	"""
	Process echo messages
	"""

	global last_wave	

	type, sequence, initiator, neighbor_pos, operation, payload = message
	wave = (sequence, initiator)
	
	window.writeln("CHECK: " + str(operation))

	# If already received  immediately send echo_reply to sender
	if((wave == last_wave)):
		window.writeln("-> Immediate reply: Double wave")
		if(operation == OP_SIZE):
			send_echo_reply_size(peer,window, message, address,1, OP_NOOP)
		else:
			send_echo_reply(peer,window, message, address)
	else:
		# Make sender father:
		global father
		father = address

		# Only 1 neighbor,  immediately send echo_reply to father
		if(len(neighbors) == 1):
			if(message[4] == OP_SIZE):
				window.writeln("-> Immediate reply: Only 1 neighbor, size")
				send_echo_reply_size(peer, window, message, father, 1)
			else:
				window.writeln("-> Immediate reply: Only 1 neighbor")
				send_echo_reply(peer,window, message, father)


		# If more neighbors, send echo to them all
		elif(len(neighbors) > 1):
			send_wave_further(peer,window, message, father)

		else:
			print "Something went wrong..."

	# Set wave as last wave

	last_wave = wave


# Process ECHO_REPLY message	
def process_echo_reply(peer, window, message, address):
	"""
	Process received MSG_ECHO_REPLY
	"""
	global echo_reply_counter
	global father
	global payload_counter
	type, sequence, initiator, neighbor_pos, operation, payload = message	

	# Increment reply counter	
	echo_reply_counter += 1

	if(message[4] == OP_SIZE):
		window.writeln("HELLO")
		window.writeln("Paycounter was: " + str(payload_counter))
		payload_counter += payload
		window.writeln("Paycounter is: " + str(payload_counter))
	

	window.writeln("Neighbors: " + str(len(neighbors)))
	window.writeln("Echo reply: " + str(echo_reply_counter))

	# Reply from all neighbors
	if(len(neighbors) == echo_reply_counter):
		payload_counter += 1
		window.writeln("->Reply from ALL neighbors")		
		# Node was initiator
		if(initiator == node_location):
			window.writeln("I AM INITIATOR! DECIDED \n")
			window.writeln("Payload = " + str(payload_counter))
			decide()
		# Send echo reply to father		
		else:
			if(message[4] == OP_SIZE):
				send_echo_reply_size(peer, window, message, father, payload_counter)				
			else:
				send_echo_reply(peer,window, message, father)
		echo_reply_counter = 0
		payload_counter = 0	

def decide():
	"""
	Echo wave stops and counter is reset
	"""
	global echo_reply_counter
	echo_reply_counter = 0

### TASK 3
def send_echo_size(peer, window):
	"""
	Initiate echo wave to gain size to neighbors
	"""
	global payload_counter
	window.writeln("INIT: " + str(payload_counter))
	# create echo message
	global sequencenumber
	pong_enc_sent = message_encode(MSG_ECHO,  sequencenumber, node_location, (-1,-1), OP_SIZE, 0)

	# Sent to all neighbors
	for i in neighbors:
		location, address = i
		peer.sendto(pong_enc_sent, address)
		
	window.writeln("-> message sent: (MSG_ECHO_REPLY," + str(sequencenumber) + "," + str(node_location) + ",(-1,-1), OP_SIZE, 0)")

	# Increment sequencenumber
	sequencenumber += 1


def send_echo_reply_size(peer, window, message, address, payload, operation = OP_SIZE):
	"""
	Send reply to sender to gain size
	"""
	pong_enc_sent = message_encode(MSG_ECHO_REPLY,  message[1], message[2], message[3], operation, payload)
	peer.sendto(pong_enc_sent, address)
	window.writeln("[S] Echo reply sent to " + str(father) + "with payload: " + str(payload))



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
		type, sequence, initiator, neighbor_pos, operation, payload = message_dec_recv	

		# Check type of message
		if(type == 1):			# Receiving PONG message
			# Add neighbor if not already in list
			neighbor = (neighbor_pos, address)
			if neighbor not in neighbors:
				neighbors.append(neighbor)

		elif(type == 2): 	# Receiving ECHO message
			window.writeln("[R] Received ECHO wave: " + str(initiator) + "\tSequence: " + str(sequence) + "from: " + str(address))		
			process_echo(peer, window, message_dec_recv, address)

		elif(type == 3):		# Receiving ECHO REPLY message
			window.writeln("[R] Received ECHO REPLY to wave: " + str(initiator) + "\tSequence: " + str(sequence) + "from: " + str(address))	
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

	global portnumber, father
	# Get socket information
	father = peer.getsockname()
	_,portnumber = father

	# Set blocking to zero
	peer.setblocking(0)
	mcast.setblocking(0)

	# Set up position node
	move()

	#TODO FOR TESTING ONLY!!
	if(len(argv) == 3):
		global nx,ny
		nx = int(argv[1])
		ny = int(argv[2])
		global node_location
		node_location = (nx,ny)

	# Send multicast PING
	send_ping(peer)

	# Set time	
	pingtime = time.time()

	give_info(window)

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
		test = command.split(" ")
		if (command == "ping"):
			window.writeln("> Command entered: " + command)
			window.writeln("Sending ping over multicast...")
			send_ping(peer)

		elif (command == "list"):
			window.writeln("> Command entered: " + command)
			list(window)

		elif (command == "move"):
			window.writeln("> Command entered: " + command)
			move()
			window.writeln("New location:" + str(node_location))
		#TODO: For testing only
		elif (test[0] == "testmove"):
			window.writeln("> Command entered: " + command)
			move(int(test[1]), int(test[2]))
			window.writeln("New location:" + str(node_location))
		#TODO: For testing only
		elif (command == "info"):
			window.writeln("> Command entered: " + command)
			give_info(window)
		elif (command == "echo"):
			window.writeln("> Command entered: " + command)
			window.writeln("Sending echo...")
			send_echo(peer, window)
		elif (command == "size"):
			window.writeln("> Command entered: " + command)
			window.writeln("Sending echo...")
			send_echo_size(peer, window)
		elif(command == "size"):
			window.writeln(">Command entered: " + command)
			window.writeln("Computing size...")
			send_echo(peer, window, OP_SIZE)

		elif (command == ""):
			pass

		else:
			window.writeln("The command \'" + str(command) + "\' is unknown.")



if __name__ == '__main__':
	sys.exit(main(sys.argv))
