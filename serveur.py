#!/usr/bin/python
# -*- encoding: utf-8 -*-

import os, sys, socket, time, signal, select
from collections import deque

# Gestion des clients (connexions/messages/déconnections) :

def gestion_connexions() :
	readers, writers, errors = select.select([serveur],[],[],0)
	for connexion in readers :
		client, addr = connexion.accept()
		pseudo = client.recv(20)		# pseudo = première chose que le serveur reçoit d'un client
		tuple_client = (client, pseudo)	# association du socket client à son pseudo
		clients_pseudos.append(tuple_client)
		clients_connectes.append(client)
		print("{} s'est connecté(e) sur {}:{}".format(pseudo, addr[0], addr[1]))
		for c in clients_connectes:
			notif_connexion = "{} s'est connecté(e)\n".format(pseudo)
			c.send(notif_connexion)	# prévenir tous les clients connectés d'une connexion

def gestion_receptions() :
	lecture_client, writers, errors = select.select(clients_connectes, [], [], 0)
	for client in lecture_client :
		message = client.recv(1024)
		if message == "{} s'est déconnecté(e)\n".format(get_pseudo(client)) :
			reponse = message
			gestion_deconnection(client)
		else :
			reponse = "{} : {}".format(get_pseudo(client), message) 	# pseudo : message
#			archiver(reponse)			# ver liste
			historique.append(reponse)	# ver deque
			ecrire_historique()
		print("\r"+reponse)
		for c in clients_connectes :
			c.send(reponse)		# envoie à tous les clients connectés

def gestion_deconnection(client) :
	i = get_index(client)
	clients_connectes.pop(i)
	clients_pseudos.pop(i)


# Gestion des requêtes HTTP pour le serveur web :

def gestion_requetes() :
	sock, a = serveur_web.accept()
	requete = sock.recv(1024).split()
	reponse = ""
	try :
		if requete[0] == "GET" :
			fichier = requete[1][1:]
			try :
				essai = os.open(fichier, os.O_RDONLY)
			except OSError :
				print("404 : {} n'a pas été trouvé".format(fichier))
				reponse = entete(404) + "{} n'existe pas !".format(fichier)
			else :
				print("200 : Une requête HTTP a été acceptée")
				reponse = entete(200) + lire(essai)
				os.close(essai)
		else :
			print("403 : Une requête HTTP a été rejetée")
			reponse = entete(403) + "<h1>Requête rejetée !</h1>"
		sock.sendall(reponse)
	except IndexError :
		pass
	sock.close()


# Retrouver le pseudo associé à un client :
def get_pseudo(client) :
	for tup in clients_pseudos :
		if client in tup :
			return tup[1]
	return None

# Retrouver l'index d'un client :
def get_index(client) :
	for i in range(len(clients_connectes)) :
		if clients_connectes[i] == client :
			return i
	return None

# Enregistrer un message dans la liste des 5 derniers :
##def archiver(message) :
##	if len(historique) > 4 :	# max = 5
##		historique.pop(0)
##	historique.append(message)

# Mettre à jour le fichier html :
def ecrire_historique() :
	liste = ""
	for message in historique :
		liste += "<li>"+message+"</li>"
	f = os.open("index.html", os.O_WRONLY | os.O_CREAT)
	os.write(f, liste)
	os.close(f)

# Lire un fichier déjà ouvert (descripteur) :
def lire(fichier) :
	contenu = ""
	tmp = " "
	while tmp != "" :
		tmp = os.read(fichier, 1024)
		contenu += tmp
	return contenu
	
# Générer un en-tête :
def entete(code) :
	res = "HTTP/1.0 "
	if (code == 200) :
		res += "200 OK\nContent-type: text/html\n"
	elif (code == 403) :
		res += "403 Forbidden\n"
	elif (code == 404) :
		res += "404 Not Found\n"
	res += "Connection: close\n\n"
	return res

# Handler de déconnection du serveur :
def fermer(signal, frame) :
	if pid == 0 :
		for client in clients_connectes :
			client.send("stop")	# signaler aux clients connectés que le serveur se déconnecte
			client.close()
		sys.exit()
	try :
		os.wait()
	except :
		pass
	serveur.close()
	serveur_web.close()
	print("\nLe serveur s'est déconnecté")
	sys.exit()

signal.signal(signal.SIGINT, fermer)
signal.signal(signal.SIGTERM, fermer)

hote = "localhost"

# Récupération des arguments :
try :
	port = int(sys.argv[1])
	port_web = int(sys.argv[2])
except IndexError :
	print("Un numéro de port est manquant")
	sys.exit()

addr = (hote, port)


### SERVEUR

# Création du serveur :
try :
	serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM,0)
except :
	print("Echec de la création du serveur")
	sys.exit()

# Connexion du serveur :
try :   
	serveur.bind(addr)
except :
	print("Echec de la connection du serveur au port {} : essayez de changer de port".format(port))
	serveur.close()
	sys.exit()
print("Le serveur s'est connecté au port {}".format(port))


### SERVEUR WEB

try :
	serveur_web = socket.socket(socket.AF_INET, socket.SOCK_STREAM,0)
except :
	print("Echec de la création du serveur web")
	serveur.close()
	sys.exit()
try :   
	serveur_web.bind((hote, port_web))
except :
	print("Echec de la connection du serveur web au port {} : essayez de changer de port".format(port_web))
	serveur_web.close()
	serveur.close()
	sys.exit()
print("Le serveur web s'est connecté au port {}".format(port_web))


# Attente de clients :
serveur.listen(5)
serveur_web.listen(5)

clients_connectes = []	# liste de socket
clients_pseudos = []	# liste de tuples (socket,pseudo)
# car on a besoin d'une liste de socket pour select.select
# mais aussi de connaitre le pseudo d'un client

# 5 derniers messages
#historique = []			# ver liste
historique = deque("", 5)	# ver deque

# Gestion parallèle des serveurs :
pid = os.fork()
while True :
	if pid == 0 :
		gestion_connexions()
		gestion_receptions()
	else :
		gestion_requetes()
