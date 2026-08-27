# Démonstration
## Lancement des tests
```
pytest -v
docker compose -f docker\docker-compose.yml up -d
pytest tests\infra\assert_commands.py -v
```

## Résolution A/AAAA
```
python -m src.client.cli_ui www.example.com -s 127.0.0.1 -p 10054
docker compose -f docker\docker-compose.yml logs resolver -n 5
python -m src.client.cli_ui www.example.com -s 127.0.0.1 -p 10054 -t AAAA
python -m src.client.cli_ui nexiste.pas.example.com -s 127.0.0.1 -p 10054
```

## Caching
```
python -m src.client.cli_ui www.example.com -s 127.0.0.1 -p 10054
python -m src.client.cli_ui www.example.com -s 127.0.0.1 -p 10054
docker compose -f docker\docker-compose.yml logs resolver -n 1
python -m src.client.cli_ui flush.cache.local -s 127.0.0.1 -p 10054 -t TXT
```

## Conformité du client avec les DNS standards
```
python -m src.client.cli_ui www.example.com -s 8.8.8.8
```

## Conformité avec `dig`
```
dig @127.0.0.1 -p 10054 www.example.com A
```

## Résolution par un serveur "hybride" (auth)
```
python -m src.client.cli_ui ns1.tld.be -s 127.0.0.1 -p 10055
docker compose -f docker\docker-compose.yml logs auth_example_ns -n 3
python -m src.client.cli_ui www.example.com -s 127.0.0.1 -p 10055
docker compose -f docker\docker-compose.yml logs auth_example_ns -n 2
```

## Hot-reloading
```
python -m src.client.cli_ui ns1.tld.org -s 127.0.0.1 -p 10054   // Attend résultat négatif
```

Mise à jour du fichier `zones/root.json` pour ajouter la zone `org.` et son NS `ns1.tld.org`.

```
docker compose -f docker\docker-compose.yml logs root_ns -n 5
docker compose -f docker\docker-compose.yml logs root_slave -n 3
```

```
python -m src.client.cli_ui ns1.tld.org -s 127.0.0.1 -p 10054   // Attend résultat négatif
python -m src.client.cli_ui flush.cache.local -s 127.0.0.1 -p 10054 -t TXT
python -m src.client.cli_ui ns1.tld.org -s 127.0.0.1 -p 10054   // Attend résultat positif
```

## Panne
```
docker compose -f docker\docker-compose.yml stop root_ns
python -m src.client.cli_ui flush.cache.local -s 127.0.0.1 -p 10054 -t TXT
python -m src.client.cli_ui ns1.tld.org -s 127.0.0.1 -p 10054   // Attend résultat positif
docker compose -f docker\docker-compose.yml logs root_slave -n 2
```

## Remise en place
```
docker compose -f docker\docker-compose.yml start root_ns
```

Remise en place du fichier `zones/root.json` pour supprimer la zone `org.` et son NS `ns1.tld.org`.

```
python -m src.client.cli_ui flush.cache.local -s 127.0.0.1 -p 10054 -t TXT
python -m src.client.cli_ui ns1.tld.org -s 127.0.0.1 -p 10054   // Attend résultat négatif
docker compose -f docker\docker-compose.yml down -v
```