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

reply_counter = 0 # Counter for replies received from neighbors

########### Task 1 #############
def setup_globals():
	# Create global variable
	# Global lists
	global neighbors, received_reply
	neighbors = []				# List of all known neighbors 
	received_reply = []			# List to keep track of received echo_reply

	# Global counters
	global sequenceNode
	sequenceNode = 0

	# Global misc
	global unknown, sensorvalue, portnumber, father
	sensorvalue = random.randint(0, 10000)
	unknown = (-1,-1)			# Used when location is unknown (father) or unnecessary (neighbors) in message
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

#TODO: Changed for testing
def move(inputx = -1, inputy = -1):
	"""
	Creates random position for node in 100 x 100 grid
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

# FOR FIRST ECHO (Task 2.1)
# Send echo first time around
def send_echo(peer,window):
	"""
	Send echo to neighbors
	"""
	global echo_reply_counter
	global sequencenumber
	sequencenumber = 0
	echo_reply_counter = 0
	pong_enc_sent = message_encode(MSG_ECHO,  sequencenumber, node_location, (-1,-1), OP_NOOP, 0)
		# Sent to all neighbors
	for i in neighbors:
		location, address = i
		peer.sendto(pong_enc_sent, address)
		
	window.writeln("MSG_ECHO_REPLY, message sent: (MSG_ECHO_REPLY," + str(sequencenumber) + "," + str(father) + "(-1,-1), OP_NOOP, 0)")
	sequencenumber += 1

def send_wave_further(peer,window, message, address):
	"""
	Send wave further to the rest of neighbors
	"""
	# set echo reply counter to 1, no reply is needed from father
	global echo_reply_counter
	echo_reply_counter = 1

	for i in neighbors:
		location, address = i
		# Do no send wave to father
		if(address != father):
			location, address = i
			pong_enc_sent = message_encode(MSG_ECHO,  message[1], message[2], message[3], message[4], message[5])
			peer.sendto(pong_enc_sent, address)
		else: 
			pass
				
# Sends reply to father
def send_echo_reply(peer,window, message, address):
	pong_enc_sent = message_encode(MSG_ECHO_REPLY,  message[1], message[2], message[3], message[4], message[5])
	peer.sendto(pong_enc_sent, address)
	window.writeln("Echo reply sent to " + str(address)) 

# Process ECHO message
def process_echo(peer, window, message, address):
	type, sequence, initiator, neighbor_pos, operation, payload = message
	wave = (sequence, initiator)

	# Set node from which you received echo as father.
	global father
	father = address

	window.writeln("Father is set. : " + str(father))

	global last_wave	
	window.writeln("LAST WAVE = " + str(last_wave))

	
	# If already received or only 1 neighbor, immediately send echo_reply to father
	if((wave == last_wave) or len(neighbors) == 1):
		if((wave == last_wave)):
			window.writeln("Immediate reply: Double wave")
		else:
			window.writeln("Immediate reply: Only 1 neighbor")
		send_echo_reply(peer,window, message, address)

	# If more neighbors, send echo to them all
	elif(len(neighbors) > 1):
		send_wave_further(peer,window, message, address)
	else:
		print "Something went wrong..."
	
	# Set wave as last wave
	last_wave = wave
		
	
# Process ECHO_REPLY message	
def process_echo_reply(peer, window, message, address):
	global echo_reply_counter
	global father

	type, sequence, initiator, neighbor_pos, operation, payload = message	
	# Increment reply counter	
	echo_reply_counter += 1
	
	window.writeln("Reply counter: "  + str(echo_reply_counter))
	window.writeln("Neighbors counter: "  + str(len(neighbors)))
	# Reply from all neighbors
	if(len(neighbors) == echo_reply_counter):
		window.writeln("Reply from ALL neighbors")		
		print 'Neighbors: ', len(neighbors)
		# Node was initiator
		if(initiator == node_location):
			window.writeln("I AM INITIATOR! DECIDED \n")
			decide()
		# Send echo reply to father		
		elif(initiator != node_location):
			send_echo_reply(peer,window, message, father)

	
# Echo wave stops and counter is reset
def decide():
	global reply_counter
	reply_counter = 0



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
			window.writeln("Received ECHO wave: " + str(initiator) + "\tSequence: " + str(sequence) + "from: " + str(address))		
			process_echo(peer, window, message_dec_recv, address)

		elif(type == 3):		# Receiving ECHO REPLY message
			window.writeln("Received ECHO REPLY to wave: " + str(initiator) + "\tSequence: " + str(sequence) + "from: " + str(address))	
			process_echo_reply(peer, window, message_dec_recv, address)
	except error:
		pass
		
		
########## TASK 3 ##########

def send_echo_size(peer, window, father):
	if(len(neighbors) == 1 and father != (-1,-1)):
		# Get address for ECHO Reply
		location, address = neighbors[0]
		# Encode message. Neighbor location not needed -> -1, -1 not possible for grid location
		pong_enc_sent = message_encode(MSG_ECHO_REPLY, father, (-1,-1), OP_SIZE, 1)
		peer.sendto(pong_enc_sent, address)	
		window.writeln("Send echo reply to: " + str(address))


	else:
		# Encode message. Neighbor location not needed -> -1, -1 not possible for grid location
		pong_enc_sent = message_encode(MSG_ECHO, node_location, (-1,-1), OP_SIZE, 1)
		# Sent to all neighbors
		for i in neighbors:
			location, address = i
			# If known father, do not send back to father
			if(father == location):
				pass
			else:
				peer.sendto(pong_enc_sent, address)

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
	#address, portnumber = peer.getsockname()
	
	global a, b
	a = 1
	b = 2

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
		elif (command == "echo"):
			window.writeln("> Command entered: " + command)
			window.writeln("Sending echo...")
			send_echo(peer, window)
		elif (command == ""):
			pass

		else:
			window.writeln("The command \'" + str(command) + "\' is unknown.")



if __name__ == '__main__':
	sys.exit(main(sys.argv))
