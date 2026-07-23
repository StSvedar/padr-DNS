### Épic 1 : L'Outil Client (CLI)

**US-1.1 : En tant qu’utilisateur, je veux pouvoir tester toutes les fonctionnalités du système depuis un client CLI afin de vérifier son bon fonctionnement.**

- **Implications techniques :**
    - Développement d'un script Python indépendant.
    - Utilisation d'une librairie standard pour le parsing des arguments en ligne de commande (ex: `argparse`, ou `click` ou `typer` plus moderne).

**US-1.2 : En tant qu'utilisateur, je veux pouvoir résoudre un nom de domaine en adresse IPv4 (Type A) afin de pouvoir me connecter au serveur cible.**

- **Implications techniques :**
    - Utilisation de sockets réseau pour communiquer en UDP et TCP (port de destination 53).
    - Développement d'un module de "forge" pour construire la trame binaire DNS.
    - Génération d'un identifiant de transaction aléatoire (Transaction ID sur 16 bits) pour l'entête, afin de faire correspondre la requête à sa réponse.

**US-1.3 : En tant qu'utilisateur, je veux pouvoir résoudre un nom de domaine en adresse IPv6 (Type AAAA) afin de pouvoir me connecter au serveur cible sur un réseau moderne.**

- **Implications techniques :**
    - Identique à l'US-1.2, avec gestion du QTYPE correspondant (28).

**US-1.4 : En tant qu'utilisateur, je veux pouvoir envoyer un signal d'administration au serveur récursif afin de vider son cache à distance pour du diagnostic.**

- **Implications techniques :**
    - Afin d'éviter l'ouverture d'un port dédié ou l'utilisation d'OpCodes non standards, envoi d'une requête DNS classique de type `TXT` ciblant un nom de domaine spécifique réservé à l'administration (ex: `flush.cache.local`).

**US-1.5 : En tant qu'utilisateur, je veux pouvoir désactiver la récursion (RD=0) via une option du CLI afin d'interroger un serveur de manière ciblée pour du diagnostic.**

- **Implications techniques :**
    - Ajout d'un paramètre (flag) dans la commande CLI qui modifie directement le bit RD (Recursion Desired) dans l'en-tête de la trame forgée.

**US-1.6 : En tant qu’utilisateur, je veux pouvoir utiliser la solution sur mon ordinateur personnel en me limitant à de la configuration réseau pour que mon ordinateur effectue les résolutions de façon transparente.**

- **Implications techniques :**
    - Respect strict du protocole binaire DNS (RFC).
    - Le serveur devra extraire correctement le tuple `(IP_Source, Port_Source)` lors de la réception des paquets (via `recvfrom`) pour renvoyer la réponse au port éphémère aléatoire utilisé par le système d'exploitation.

### Épic 2 : Le Serveur Récursif (Le Chef d'orchestre)

**US-2.1 : En tant que résolveur, je veux écouter sur le port UDP 53 et désérialiser la trame binaire entrante afin d'extraire le nom de domaine et le type de requête demandés.**

- **Implications techniques :**
    - Création d'une socket UDP en écoute sur le port 53.
    - Développement d'un parseur binaire utilisant la librairie standard `struct` pour décompresser et interpréter les octets bruts.

**US-2.2 : En tant que résolveur, je veux interroger mon cache interne avant d'émettre une requête sur le réseau afin d'accélérer drastiquement le temps de réponse.**

- **Implications techniques :**
    - Structure de données en RAM (dictionnaire Python).
    - La clé du dictionnaire doit être un tuple `(Nom_de_domaine, Type_de_requête)` pour différencier les réponses IPv4 et IPv6 d'un même domaine.

**US-2.3 : En tant que résolveur, je veux implémenter la boucle de délégation (Root -> TLD -> Autorité) afin de trouver la réponse à la requête.**

- **Implications techniques :**
    - Mécanisme itératif (boucle ou fonction récursive) orchestrant les appels réseau.
    - Utilisation d'une socket avec un port source éphémère (attribué par l'OS) pour envoyer les requêtes vers le port 53 des serveurs d'autorité.

**US-2.4 : En tant que résolveur, je veux extraire le TTL des réponses positives (A/AAAA) et les stocker en mémoire afin de construire mon cache.**

- **Implications techniques :**
    - Extraction du TTL par le parseur.
    - Stockage en cache sous forme de tuple `(Données, Timestamp_Expiration)`.
    - Implémentation d'une Lazy Expiration : la validité du TTL est vérifiée uniquement au moment où l'entrée est lue/accédée, déclenchant une suppression si le délai est dépassé (évitant ainsi des threads de nettoyage complexes).

**US-2.5 : En tant que résolveur, je veux lire l'enregistrement SOA lors d'une erreur NXDOMAIN afin de mettre cette absence en cache (Negative Caching).**

- **Implications techniques :**
    - Capacité du dictionnaire à stocker une valeur représentant une absence (flag `NXDOMAIN`).
    - Extraction du "Minimum TTL" situé à la fin de l'enregistrement SOA de la section d'autorité.

**US-2.6 : En tant que résolveur, si une réponse UDP contient le flag TC=1 (Tronqué), je veux relancer automatiquement ma requête via TCP afin d'obtenir la donnée complète.**

- **Implications techniques :**
    - Ouverture d'une socket TCP vers le port 53.
    - Respect de l'encapsulation DNS sur TCP : nécessité d'ajouter un préfixe de 2 octets indiquant la longueur totale du message avant d'envoyer la trame.

**US-2.7 : En tant que résolveur, je veux intercepter les messages d'administration du client afin de vider instantanément ma structure de données de cache en RAM.**

- **Implications techniques :**
    - Détection conditionnelle dans le parseur (ex: intercepter la requête ciblée sur `flush.cache.local`).
    - Fonction de réinitialisation du dictionnaire système (`cache.clear()`).

### Épic 3 : Le Serveur de Noms (Root, TLD, Autorité)

**US-3.1 : En tant que serveur de nom, je veux charger ma base de données (Zone) depuis un fichier JSON au démarrage afin de connaître les enregistrements sous ma responsabilité.**

- **Implications techniques :**
    - Choix du format JSON justifié par l'architecture : données chargées une seule fois en RAM pour des accès rapides, opérations majoritairement en lecture, format lisible et éditable manuellement.
    - Normalisation des données au chargement (conversion de tous les noms de domaine en minuscules pour assurer une correspondance insensible à la casse).

**US-3.2 : En tant que serveur de nom, si la requête correspond à une IP que je connais, je veux renvoyer une réponse autoritaire (AA=1) contenant la ou les IP (RRSets) dans la section Answer.**

- **Implications techniques :**
    - Paramétrage spécifique du module de sérialisation pour positionner le flag AA.
    - Boucle pour construire de multiples Resource Records si plusieurs adresses IP existent pour un même domaine.

**US-3.3 : En tant que serveur de nom, si je ne gère qu'une portion du domaine (ex: Root ou TLD), je veux renvoyer une délégation (enregistrement NS) dans la section Authority afin que le serveur récursif puisse continuer sa recherche.**

- **Implications techniques :**
    - Analyse syntaxique du domaine demandé pour identifier le découpage logique.
    - Paramétrage du sérialiseur pour peupler la section *Authority* sans modifier la section *Answer*.

**US-3.4 : En tant que serveur de nom, lors d'une délégation, je veux inclure l'adresse IP du serveur délégué dans la section Additional (Glue Record) afin de faire gagner du temps au résolveur.**

- **Implications techniques :**
    - Recherche interne de l'adresse IP associée au nom du serveur NS.
    - Paramétrage du sérialiseur pour peupler la section *Additional*.

**US-3.5 : En tant que serveur de nom, je veux implémenter l'algorithme de compression (pointeur 11xxxxxx) lors de la création de ma réponse binaire afin de ne pas saturer la limite de 512 octets de l'UDP.**

- **Implications techniques :**
    - Développement d'un algorithme de compression au sein du sérialiseur.
    - Maintien d'un dictionnaire temporaire d'offsets (`{'nom_de_domaine': position_octet}`) durant la construction du paquet pour remplacer les occurrences répétées par des pointeurs sur 2 octets.

**US-3.6 : En tant qu'administrateur, je veux pouvoir déclencher le rechargement du fichier JSON "à chaud" (sans redémarrer le processus du serveur) afin d'ajouter ou modifier des enregistrements sans provoquer d'interruption de service.**

- **Implications techniques :**
    - Capture asynchrone d'un signal système via la librairie standard `signal` (ex: intercepter `SIGHUP` sur les systèmes UNIX).
    - Exécution d'une fonction de rechargement écrasant le dictionnaire en mémoire de manière thread-safe.

### Épic 4 : Tolérance aux Pannes & Réplication (Master / Slave)

**US-4.1 : En tant que serveur Racine Réplica (Slave), je veux me connecter en TCP au serveur Racine Master à mon démarrage et demander un transfert de zone complet (AXFR) afin d'obtenir la configuration initiale.**

- **Implications techniques :**
    - Construction d'une requête DNS standard (OpCode 0) mais utilisant le QTYPE `252` (AXFR).
    - Envoi et réception via TCP avec gestion stricte du préfixe de longueur (2 octets).

**US-4.2 : En tant que serveur Racine Master, je veux accepter les requêtes de type AXFR en TCP et renvoyer l'intégralité de mon fichier de zone afin d'assurer la redondance requise.**

- **Implications techniques :**
    - Détection du QTYPE 252.
    - Boucle itérant sur l'intégralité du dictionnaire de zone pour convertir toutes les entrées en un flux continu de Resource Records sérialisés sur la connexion TCP ouverte.

**US-4.3 : En tant que serveur Racine Master, lorsque mon fichier JSON est modifié, je veux envoyer un message UDP (OpCode 4, NOTIFY) à mon Slave afin de le prévenir instantanément d'un changement.**

- **Implications techniques :**
    - Construction d'une trame avec OpCode=4 envoyée à l'IP et au port 53 configurés pour le Slave.
    - Attente d'un accusé de réception (QR=1) de la part du Slave.

**US-4.4 : En tant que serveur Racine Réplica (Slave), à la réception d'un NOTIFY ou après l'expiration de mon timer de Refresh, je veux comparer mon numéro de série (SOA) avec celui du Master afin de savoir si je dois me mettre à jour.**

- **Implications techniques :**
    - Extraction et comparaison d'entiers (Serial Number) entre la version locale et la version distante.

**US-4.5 : En tant que serveur Racine Réplica, si le numéro de série du Master est plus grand, je veux effectuer une requête de transfert afin de télécharger les nouveaux enregistrements.**

- **Implications techniques :**
    - Afin de garantir la robustesse de l'architecture sans implémenter un historique complexe de versions de zone (requis pour un transfert incrémental IXFR), le système déclenchera un nouveau transfert de zone complet (AXFR) remplaçant la configuration actuelle.

### Épic 5 : Environnement, Qualité et Méthodologie (En tant que Dev)

**US-5.1 : En tant que développeur, je veux qu’un pipeline d'Intégration Continue exécute automatiquement mes tests unitaires à chaque push afin de valider la non-régression de mon code.**

- **Implications techniques :**
    - Configuration d'un fichier `.gitlab-ci.yml`.
    - Utilisation d'un framework de tests (comme `pytest`).
    - Écriture de tests unitaires ciblant prioritairement la logique pure (la "Forge" : Parser et Serializer) en validant les entrées/sorties d'octets statiques, indépendamment des appels réseau, pour garantir la stabilité de l'intégration continue.