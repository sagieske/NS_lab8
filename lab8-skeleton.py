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

def send_ping(initiator_location, peer):
	"""
	Send mulitcast ping
	"""
	#1.1: Send multicast PING with initiators location 
	#Seq number set to 0 with ping, neighbour is set to -1,-1 since this is off the grid)
	ping_enc_sent = message_encode(MSG_PING, 0, initiator_location, (-1,-1))
	peer.sendto(ping_enc_sent, (MCAST_GRP, MCAST_PORT))
	

def move():
	"""
	Creates random position for node in 100 x 100 grid
	"""
	global x, y
	x = random.randint(0, 100)
	y = random.randint(0, 100)
	return (x,y)

def list():
	print "\nNEIGHBOUR INFORMATION:"
	for i in neighbours:
		location, port = i
		print "\nPosition:\t" + str(location) +  "\nIP:port :\t" + str(port)


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

	#---- 
	# Create global variable
	global neighbours, radius, sensorvalue, portnumber
	neighbours = []
	radius = 50
	sensorvalue = random.randint(0, 10000)

	# Get socket information
	ip, portnumber = peer.getsockname()
	# Choose random position
	initiator_location = move()

	# Print out information 
	print "INFORMATION\nIP:port:\t" + str(portnumber) + "\nPosition:\t" + str(initiator_location) + "\nSensor Value:\t" + str(sensorvalue) + "\n"

	# Send multicast PING
	send_ping(initiator_location, peer)




	#1.2: Check if receive PING from multicast, if so send back PONG TODO: range!
	#TODO: if (mcast.recvfrom(10240)):
	ping_enc_recv, address = mcast.recvfrom(10240)
	ping_dec_recv = message_decode(ping_enc_recv)
	type, _, initiator, _, _, _ = ping_dec_recv	#only PING can be sent on mcast
	print "PING multicast received."

	#Check if PING is not from itself:
	ip_ping, port_ping = address
	if (portnumber == port_ping): 
		print "EIGEN BERICHT, stop"
	else: 
		print "NIET EIGEN BERICHT, verstuur pong"

	#TODO: check if PING is within range
	pong_enc_sent = message_encode(MSG_PING, 0, initiator, initiator_location)
	peer.sendto(pong_enc_sent, address)
	print "PONG sent"

	#1.3 Check if receive PONG, add position and remote IP:port adress to list neighbours
	pong_enc_rec, (address, port) = peer.recvfrom(10240)
	pong_dec_recv = message_decode(pong_enc_rec)
	print "PONG received"
	type, _, initiator, neighbour_pos, _, _ = pong_dec_recv	#only PING can be sent on mcast
	neighbour = (neighbour_pos, port)
	neighbours.append(neighbour)
	print "Neighbours added"
	list()	
	
	#while window.update():
	#	pass



if __name__ == '__main__':
	sys.exit(main(sys.argv))
