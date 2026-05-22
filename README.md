# odoo-on-dokploy

Questo repository è un boilerplate minimale per avviare un'istanza Odoo usando Docker Compose e provarne il deployment con un reverse-proxy (es. Traefik). È pensato per scopi di sviluppo e test.

## A cosa serve
- Fornire un ambiente Docker pronto per eseguire Odoo (default: Odoo 18) con PostgreSQL come database.
- Permettere il montaggio di moduli personalizzati tramite la cartella `addons/`.
- Mostrare un esempio di integrazione con Traefik (label per router, TLS/ACME e WebSocket).

## Struttura del progetto
- `docker-compose.yml` - definisce i servizi `db` (Postgres) e `web` (Odoo) e i volumi usati.
- `addons/` - cartella locale da montare in Odoo come `extra-addons` per i moduli custom.
- `config/odoo.conf` - file di configurazione Odoo (montato nel container). Contiene la password dell'admin e le impostazioni minime.

## Template repository e naming consigliato
- Rinominare il repository base in `odoo18-template`.
- Abilitare l'opzione GitHub **Template repository** così i nuovi progetti vengono creati con **Use this template**.
- Usare la naming convention `odoo18-[nomecliente]` per i repository derivati.
- La GitHub Action di build pubblica automaticamente l'immagine `ghcr.io/<owner>/<repository>:latest`, quindi il nome del repository diventa parte del tag Docker.

## Prerequisiti
- Docker e Docker Compose installati sulla macchina host.
- Una rete Docker esterna chiamata `dokploy-network` (puoi crearla con `docker network create dokploy-network`).
- (Opzionale) Traefik in esecuzione e connesso alla stessa rete `dokploy-network` per sfruttare le label di routing e TLS.

## Come avviare (rapido)
1. Assicurati che la rete Docker esterna esista:

```powershell
docker network create dokploy-network
```

2. Copia `.env.example` in `.env` e configura almeno `PROJECT_NAME`, `DOMAIN`, `COMPOSE_PROJECT_NAME=${PROJECT_NAME}`, `ODOO_IMAGE`, `POSTGRES_PASSWORD` e `ODOO_ADMIN_PASSWD`. Verifica di usare Docker Compose con supporto all'espansione delle variabili nel file `.env`, così `COMPOSE_PROJECT_NAME` eredita correttamente il valore di `PROJECT_NAME`.

3. Avvia lo stack:

```powershell
docker-compose up -d
```

4. Controlla i log del servizio `odoo` per verificare che Odoo sia partito correttamente:

```powershell
docker-compose logs -f odoo
```

Se Odoo è avviato correttamente vedrai nei log l'indicazione che il server HTTP è in ascolto sulla porta `8069`.

## Configurazione della password amministratore
La password amministratore è gestita tramite la variabile `ODOO_ADMIN_PASSWD` nel file `.env`. Il template `config/odoo.conf` viene renderizzato a runtime dal container con `envsubst`, così nessuna credenziale rimane hardcoded nel repository.

## Note su Traefik e routing
- Il `docker-compose.yml` usa label Traefik dinamiche basate su `PROJECT_NAME` e `DOMAIN`, così più istanze Odoo possono convivere sullo stesso nodo Dokploy.
- Il traffico HTTP/HTTPS passa da Traefik via rete Docker interna: il servizio `odoo` non espone più porte host con `ports`.
- Odoo continua a servire l'applicazione principale sulla porta interna `8069`, mentre il router WebSocket/longpolling inoltra `/websocket` verso la porta interna `8072`.
- Verifica che Traefik sia connesso alla rete `dokploy-network` e che il provider Docker sia abilitato, altrimenti Traefik non vedrà i container Odoo.
- Controlla che porte 80/443 siano aperte sull'host se usi ACME/Let's Encrypt.

## Debug rapido
- `docker-compose ps` - vedere lo stato dei container.
- `docker-compose logs odoo` - guardare i log di Odoo.
- `docker network inspect dokploy-network` - confermare che Traefik e Odoo siano sulla stessa rete.
- `curl -H "Host: il-tuo-dominio" http://<indirizzo-traefik>` - testare il routing verso Traefik con l'header Host corretto.

## Ulteriori miglioramenti suggeriti
- Aggiungere gestione dei certificati e/o backup dei volumi.

---

File creati/modificati in questa repo per risolvere un problema noto con la CLI di Odoo:
- `config/odoo.conf` (aggiunto) - usa variabili d'ambiente renderizzate a runtime invece di credenziali hardcoded.

Se vuoi, posso mostrarti i comandi PowerShell esatti per il debug o applicare altre migliorie (es. template per variabili d'ambiente).
