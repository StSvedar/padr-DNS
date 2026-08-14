# PADR
## Contexte
Ce projet a été réalisé dans le cadre du cours de programmation d'applications distribuées en réseau.
Il consiste en l'implémentation "from scratch" d'un système DNS avec tests et autres artefacts de la méthodologie SCRUM.

## Prérequis
Pour lancer le projet, vous aurez besoin de :
- Une installation standard de python
- Docker et Docker Compose
- *Optionnellement :* `dig` pour tester la conformité avec un outil standard

## Lancement des tests unitaires
Activation de l'environnement virtuel :
```
python -m venv venv       # Premier lancement uniquement
source venv/bin/activate  # Linux / MacOS
venv\Scripts\activate     # Windows
```

Installation des dépendances :
```
pip install -r requirements.txt
```

Lancement des tests :
```
pytest -v
```

## Lancement de l'infrastructure de test
Lancement :
```
docker compose -f docker\docker-compose.yml up --build -d
```

Suppression :
```
docker compose -f docker\docker-compose.yml down -v
```

Le résolveur récursif est désormais joignable localement sur le port 10054.

## Utilisation du client custom
Pour lancer différentes requêtes, vous pouvez utiliser le client custom fourni dans le projet.

Exemple :
```
python -m src.client.cli_ui www.example.com -s 127.0.0.1 -p 10054
python -m src.client.cli_ui www.example.com -s 127.0.0.1 -p 10054 -t AAAA
python -m src.client.cli_ui nexiste.pas.example.com -s 127.0.0.1 -p 10054
python -m src.client.cli_ui flush.cache.local -s 127.0.0.1 -p 10054 -t TXT
```

## Test avec l'outil standard `dig`
Pour vérifier l'interopérabilité de la solution, vous pouvez lancer une requête en utilisant l'outil standard `dig`. 

Exemple :
```
dig @127.0.0.1 -p 10054 api.example.com A
```

## Tests d'infrastructure automatisés
Activation de l'environnement virtuel et installation des dépendances :
```
python -m venv venv       # Premier lancement uniquement
source venv/bin/activate  # Linux / MacOS
venv\Scripts\activate     # Windows
```

Lancement des tests :
```
pytest tests\infra\assert_commands.py -v
```