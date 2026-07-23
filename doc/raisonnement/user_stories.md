### Épic 1 : L'Outil Client (CLI)

- **US-1.1 :** En tant qu'utilisateur, je veux pouvoir tester toutes les fonctionnalités du système depuis un client CLI afin de pouvoir vérifier son bon fonctionnement.
- **US-1.2 :** En tant qu'utilisateur, je veux pouvoir résoudre un nom de domaine en adresse IPv4 (Type A) afin de pouvoir me connecter au serveur cible.
- **US-1.3 :** En tant qu'utilisateur, je veux pouvoir résoudre un nom de domaine en adresse IPv6 (Type AAAA) afin de pouvoir me connecter au serveur cible sur un réseau moderne.
- **US-1.4 :** En tant qu'utilisateur, je veux pouvoir envoyer un signal d'administration au serveur récursif afin de vider son cache à distance pour du diagnostic.
- **US-1.5 :** En tant qu'utilisateur, je veux pouvoir désactiver la récursion (`RD=0`) via une option du CLI afin d'interroger un serveur de manière ciblée pour du diagnostic.
- **US-1.6 :** En tant qu'utilisateur, je veux pouvoir utiliser la solution sur mon ordinateur personnel en me limitant à de la configuration réseau pour que mon ordinateur effectue les résolutions de façon transparente.

### Épic 2 : Le Serveur Récursif (Le Chef d'orchestre)

- **US-2.1 :** En tant que résolveur, je veux écouter sur le port UDP 53 et désérialiser la trame binaire entrante afin d'extraire le nom de domaine et le type de requête demandés.
- **US-2.2 :** En tant que résolveur, je veux interroger mon cache interne avant d'émettre une requête sur le réseau afin d'accélérer drastiquement le temps de réponse.
- **US-2.3 :** En tant que résolveur, je veux implémenter la boucle de délégation (Root -> TLD -> Autorité) afin de trouver la réponse à la requête.
- **US-2.4 :** En tant que résolveur, je veux extraire le TTL des réponses positives (A/AAAA) et les stocker en mémoire afin de construire mon cache.
- **US-2.5 :** En tant que résolveur, je veux lire l'enregistrement SOA lors d'une erreur *NXDOMAIN* afin de mettre cette absence en cache (Negative Caching).
- **US-2.6 :** En tant que résolveur, si une réponse UDP contient le flag `TC=1` (Tronqué), je veux relancer automatiquement ma requête via TCP afin d'obtenir la donnée complète.
- **US-2.7 :** En tant que résolveur, je veux intercepter les messages d'administration du client afin de vider instantanément ma structure de données de cache en RAM.

### Épic 3 : Le Serveur de Noms (Root, TLD, Autorité)

- **US-3.1 :** En tant que serveur de nom, je veux charger ma base de données (Zone) depuis un fichier JSON au démarrage afin de connaître les enregistrements sous ma responsabilité.
- **US-3.2 :** En tant que serveur de nom, si la requête correspond à une IP que je connais, je veux renvoyer une réponse autoritaire (`AA=1`) contenant la ou les IP (RRSets) dans la section *Answer*.
- **US-3.3 :** En tant que serveur de nom, si je ne gère qu'une portion du domaine (ex: Root ou TLD), je veux renvoyer une délégation (enregistrement NS) dans la section *Authority* afin que le serveur récursif puisse continuer sa recherche.
- **US-3.4 :** En tant que serveur de nom, lors d'une délégation, je veux inclure l'adresse IP du serveur délégué dans la section *Additional* (Glue Record) afin de faire gagner du temps au résolveur.
- **US-3.5 :** En tant que serveur de nom, je veux implémenter l'algorithme de compression (pointeur `11xxxxxx`) lors de la création de ma réponse binaire afin de ne pas saturer la limite de 512 octets de l'UDP.
- **US-3.6 :** En tant qu'administrateur, je veux pouvoir déclencher le rechargement du fichier JSON "à chaud" (sans redémarrer le processus du serveur) afin d'ajouter ou modifier des enregistrements sans provoquer d'interruption de service.

### Épic 4 : Tolérance aux Pannes & Réplication (Master / Slave)

- **US-4.1 :** En tant que serveur Racine Réplica (Slave), je veux me connecter en TCP au serveur Racine Master à mon démarrage et demander un transfert de zone complet (AXFR) afin d'obtenir la configuration initiale.
- **US-4.2 :** En tant que serveur Racine Master, je veux accepter les requêtes de type AXFR en TCP et renvoyer l'intégralité de mon fichier de zone afin d'assurer la redondance requise.
- **US-4.3 :** En tant que serveur Racine Master, lorsque mon fichier JSON est modifié, je veux envoyer un message UDP (OpCode 4, NOTIFY) à mon Slave afin de le prévenir instantanément d'un changement.
- **US-4.4 :** En tant que serveur Racine Réplica (Slave), à la réception d'un NOTIFY ou après l'expiration de mon timer de Refresh, je veux comparer mon numéro de série (SOA) avec celui du Master afin de savoir si je dois me mettre à jour.
- **US-4.5 :** En tant que serveur Racine Réplica, si le numéro de série du Master est plus grand, je veux effectuer une requête de transfert incrémental (IXFR) en TCP pour télécharger uniquement les nouveaux enregistrements.

### Épic 5 : Environnement, Qualité et Méthodologie (En tant que Dev)

- **US-5.1 :** En tant que développeur, je veux qu'un pipeline d'Intégration Continue exécute automatiquement mes tests unitaires à chaque push afin de valider la non-régression de mon code.