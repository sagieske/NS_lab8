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
			# Add neighbor
			neighbor = (neighbor_pos, address)
			neighbors.append(neighbor)
			
		elif(type == 2): 	# Receiving ECHO message
			window.writeln("Message ECHO \'" + str(type) + "\' received from: " + str(initiator) + "\tSequence: " + str(sequence))	
			receive_wave(peer, window, message_dec_recv)				
			send_echo(peer, window, initiator, sequence)			
			#process_echo

		elif(type == 3):		# Receiving ECHO REPLY message
			window.writeln("Message ECHO REPLY \'" + str(type) + "\' received from: " + str(initiator) + "\tSequence: " + str(sequence))	
			
	except error:
		pass


########### Task 2 #############

# FOR FIRST ECHO (Task 2.1)
def send_echo(peer,window, father = (-1,-1), seqnumber = 0):
	"""
	Send echo to all neighbors
	"""

	# Only 1 neighbor and already known father, send echo reply
	if(len(neighbors) == 1 and father != (-1,-1)):
		# Get address for ECHO Reply
		location, address = neighbors[0]
		# Encode message. Neighbor location not needed -> -1, -1 not possible for grid location
		pong_enc_sent = message_encode(MSG_ECHO_REPLY,  seqnumber, father, (-1,-1), OP_NOOP)
		peer.sendto(pong_enc_sent, address)
		window.writeln("Echo sent echo reply to : " + str(father) + "\tSequence: " + str(seqnumber))	

	# Not known father or multiple neighbors, create new wave
	else:
		# Increase seqnumber when not initial wave
		if( father != (-1,-1)):
			seqnumber += 1
			window.writeln("NEW WAVE with " + str(seqnumber))

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
				#window.writeln("Send echo to port: " + str(address))

		# Debug line
		window.writeln("Echo sent with init from: " + str(node_location) + "\tSequence: " + str(seqnumber))	


# 2.4
"""
When a non-initiator receives an ECHO from the same wave again, send an ECHO_REPLY to sender.
"""
def receive_wave(peer, window, message_dec_recv):
	"""

	"""

	type, sequence, initiator, neighbor_pos, _, _ = message_dec_recv	
	# If ECHO from same wave already recieved, send ECHO_REPLY
	# FIXME: how to check already_recieved?
	if(len(received_waves) != 0):
		for recv_echo in received_waves:
			seq_echo, initiator_echo = recv_echo
			# Echo has been received previously, send echo reply
			if(sequence == seq_echo and initiator_echo == initiator):		
				pong_enc_sent = message_encode(MSG_ECHO_REPLY, sequence, initiator, (-1,-1), OP_NOOP, 0)
				window.writeln("ECHO DUBBLE") 
				break
	"""
	# Else if REPLY, count replies
	elif(type == MSG_ECHO_REPLY):
		for i in neighbors:
			location, address = i
			if(location == neighbor):
				reply_counter += 1
		if(reply_counter == neighbors):
			pong_enc_sent = message_encode(MSG_ECHO_REPLY, _, initiator, _, OP_NOOP, 0)
	"""		
	# Add wave to received
	received_waves.append((sequence,initiator))		
	window.writeln("TESTING - receive wave")

# 2.5
"""
When non-initiator recieved ECHO_REPLY from all neighbours, send ECHO_REPLY to father.
"""

#TODO: WORK IN PROGRESS
""" WORK IN PROGRES
def process_echo(peer, window, message, address):

	type, sequence, initiator, neighbor_pos, operation, payload = message
	wave = (sequence, initiator)


	# Only one neighbor
	if(len(neighbor) == 1):
		# Encode message
		echorep_enc_sent = message_encode(MSG_ECHO_REPLY,  sequence, initiator, neighbor_pos, operation, payload)
		peer.sendto(echorep_enc_sent, address)
		return

	for i in received_waves:
		# Wave already received previously or only one neighbor
		if( i == wave or len(neighbor) == 1):
			# Encode message
			echorep_enc_sent = message_encode(MSG_ECHO_REPLY,  sequence, initiator, neighbor_pos, operation, payload)
			# Send echo reply			
			peer.sendto(echorep_enc_sent, address)
			# Stop function
			return
	
	# Function has not been stopped, so wave has not been previously received and neighbor length > 1.
	# TODO: SEND ECHO FURTHER
	If first time:
		Add wave to received waves list
			If Only One neighbor:
				-> Send ECHO_REPLY
			Else:		
				-> Wave further ?with sequence +1? (SEND ECHO)
		If second time:
				-> Send ECHO_REPLY
"""
		



		


# 2.6
"""
When initiator received ECHO_REPLY from all neighbours, terminate algorithm.
"""




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
	# Create global variable
	global neighbors, sensorvalue, portnumber
	global received_waves, received_reply, reply_counter
	global unknown
	neighbors = []
	sensorvalue = random.randint(0, 10000)
	received_waves = []			# List to keep track of received waves
	received_reply = []			# List to keep track of received echo_reply
	reply_counter = 0			# Counter for replies received from neighbors
	unknown = (-1,-1)			# Used when location is unknown (father) or unnecessary (neighbors) in message

	# Get socket information
	_, portnumber = peer.getsockname()

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
			neighbors = []
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
