# Netwerken en Systeembeveiliging
# Lab 8 - Distributed Sensor Network
# Author(s) and student ID(s):
# Group: Eszter Fodor (5873320) & Sharon Gieske (6167667), group 15
# Date: 10-12-2012
import sys
import struct
import random
from gui import MainWindow
from sensor import *
from socket import *



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

	#create global variable
	global neighbours
	neighbours = []

	global x, y, radius
	x = random.randint(0, 100)
	y = random.randint(0, 100)
	radius = 50


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


	#TODO: In time frame of 5 sec:
	#TODO: Send multicast ping
	#TODO: If receive pong, add position and remote IP:port adress to list neighbours

	#1.1: Send multicast PING with initiators location
	message = str(MSG_PING) + "," + str((x,y))
	peer.sendto(message, (MCAST_GRP, MCAST_PORT))
	print "PING multicastsent. :" + message

	#1.2: Check if receive PING from multicast, if so send back PONG TODO: range!
	#if (mcast.recvfrom(10240)):
	ping_recv, address = mcast.recvfrom(10240)
	print "PING multicast received."
	#TODO Check if PING is not from itself:
	pong_sent = str(MSG_PONG) + "," + str((x,y))
	peer.sendto(pong_sent, address)
	print "PONG sent"

	#1.3 Check if receive PONG, add remote IP:port adress to list neighbours
	pong_recv, (address, port) = peer.recvfrom(10240)
	print "PONG received"
	print pong_recv
	print port
	neighbours.append(port)
	print "Neighbours added"
	print neighbours	

	while window.update():
		pass



if __name__ == '__main__':
	sys.exit(main(sys.argv))
