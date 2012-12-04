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
	print "SEND_PONG ready"

def move():
	"""
	Creates random position for node in 100 x 100 grid
	"""
	global nx, ny,  node_location
	nx = random.randint(0, 100)
	ny = random.randint(0, 100)
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

	#---------- BEGIN EIGEN CODE
	# Create global variable
	global neighbors, radius, sensorvalue, portnumber
	neighbors = []
	radius = 50
	sensorvalue = random.randint(0, 10000)

	# Get socket information
	_, portnumber = peer.getsockname()

	# Set blocking to zero
	peer.setblocking(0)
	mcast.setblocking(0)

	# Choose random position
	move()

	# Print out information in gui
	window.write("INFORMATION\nIP:port:\t" + str(portnumber) + "\nPosition:\t" + str(node_location) + "\nSensor Value:\t" + str(sensorvalue) + "\n")

	# Send multicast PING
	send_ping(peer)
	
	# Set time	
	pingtime = time.time()

	while window.update():
		# Resend PING if time > 5s, reset
		if(time.time() - 5 > pingtime):
			neighbors = []
			send_ping(peer)
			pingtime = time.time()
			window.writeln("RESET")
		
		# Check for multicast message
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
			elif( distance > math.pow(radius,2)):
				window.writeln("NOT IN RANGE:")
				window.writeln( "node: "+str((nx, ny)) + "\t initiator" + str((ix,iy)))
				window.writeln( "radius =" + str(radius))
				window.writeln( "distance =" + str(distance))
				window.writeln( "c =" + "root(" + str(math.pow(abs(ny-iy),2)) + " * " + str(math.pow(abs(nx-ix),2)) + ")")

				pass
			# Initiator is in same range
			else:
				window.writeln("PONG")
				send_pong(peer, initiator, address_mcast)

		
		except error:
			pass

		# receive pong
		try:
			pong_enc_rec, (address, port) = peer.recvfrom(10240)
			
			# Decode message
			pong_dec_recv = message_decode(pong_enc_rec)
			type, _, initiator, neighbor_pos, _, _ = pong_dec_recv	
	
			# Add neighbor
			neighbor = (neighbor_pos, port)
			neighbors.append(neighbor)
			window.writeln("Neighbor added.")
		except error:
			pass

		# Get commands
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
		elif (command == ""):
			pass
		else:
			window.writeln("The command \'" + str(command) + "\' is unknown.")



if __name__ == '__main__':
	sys.exit(main(sys.argv))
