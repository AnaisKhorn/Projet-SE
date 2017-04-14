#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys, socket, signal, os

# Gestion de l'envoi de messages au serveur :
def envoyer(clisock) :
	message = sys.stdin.readline()
	if message != "" :
		try :
			clisock.send(message)
		except :
			print("Echec de l'envoi de : {}".format(message))
	else :
		os.kill(0, signal.SIGQUIT)

# Gestion de réception de messages du serveur :
def recevoir(clisock) :
	reponse = clisock.recv(1024)
	if reponse == "stop" :			# si déconnection du serveur
		os.kill(0, signal.SIGTERM) 	# alors déconnection du client
	elif reponse != "{} s'est connecté(e)\n".format(pseudo) :	# le client ne reçoit pas sa propre notif de connexion
		sys.stdout.write("{}".format(reponse))

# Handler de déconnection du client :
def deconnection(signal, frame) :
	if pid == 0 :
		sys.exit()	# fin du processus fils
	try :
		os.wait()	# attente de la fin du fils (si non fini)
	except :
		pass
	try :
		client.send("{} s'est déconnecté(e)\n".format(pseudo))
	except :
		pass		# quand le serveur se déconnecte avant le client on ne peut plus rien lui envoyer
	print("\nVous êtes déconnecté(e)")
	client.close()
	sys.exit()

signal.signal(signal.SIGINT, deconnection)
signal.signal(signal.SIGQUIT, deconnection)
signal.signal(signal.SIGTERM, deconnection)

# Récupération des arguments :
try :
	hote = sys.argv[1]
	port = int(sys.argv[2])
except IndexError :
	print("Arguments manquants")
	sys.exit()
try :
	pseudo = sys.argv[3]
except IndexError :
	pseudo = "Anonyme"

# Création du socket :
try : 
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
except :
    print("Echec de la création du client")
    sys.exit()

# Connexion au serveur :
try :    
	client.connect((hote, port))
	print("Bonjour %s ! Vous êtes connecté(e) sur le port %s" %(pseudo, port))
except :
	print("Echec de la connexion au port {} : vous n'avez peut-être pas indiqué le bon port".format(port))
	client.close()
	sys.exit()
client.send(pseudo)

# Mise en attente d'envoi et de réception :
pid = os.fork()
while True :
	if pid == 0 :
		recevoir(client)
	else :
		envoyer(client)
