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

## Prerequisiti
- Docker e Docker Compose installati sulla macchina host.
- Una rete Docker esterna chiamata `dokploy-network` (puoi crearla con `docker network create dokploy-network`).
- (Opzionale) Traefik in esecuzione e connesso alla stessa rete `dokploy-network` per sfruttare le label di routing e TLS.

## Come avviare (rapido)
1. Assicurati che la rete Docker esterna esista:

```powershell
docker network create dokploy-network
```

2. Avvia lo stack:

```powershell
docker-compose up -d
```

3. Controlla i log del servizio web per verificare che Odoo sia partito correttamente:

```powershell
docker-compose logs -f web
```

Se Odoo è avviato correttamente vedrai nei log l'indicazione che il server HTTP è in ascolto sulla porta `8069`.

## Configurazione della password amministratore
La password amministratore è gestita tramite `config/odoo.conf` (chiave `admin_passwd`). Per cambiarla modifica `config/odoo.conf` e riavvia il container `web`.

## Note su Traefik e routing
- Il `docker-compose.yml` contiene label di esempio per Traefik (Host, entrypoints, certificati Let's Encrypt, router WebSocket). Queste label contengono un hostname di test e vanno adattate al tuo dominio reale.
- Verifica che Traefik sia connesso alla rete `dokploy-network` e che il provider Docker sia abilitato, altrimenti Traefik non vedrà i container Odoo.
- Controlla che porte 80/443 siano aperte sull'host se usi ACME/Let's Encrypt.

## Debug rapido
- `docker-compose ps` - vedere lo stato dei container.
- `docker-compose logs web` - guardare i log di Odoo.
- `docker network inspect dokploy-network` - confermare che Traefik e Odoo siano sulla stessa rete.
- `curl -H "Host: il-tuo-dominio" http://<indirizzo-traefik>` - testare il routing verso Traefik con l'header Host corretto.

## Ulteriori miglioramenti suggeriti
- Parametrizzare le label Traefik con variabili d'ambiente o rimuovere l'hostname hard-coded.
- Aggiungere gestione dei certificati e/o backup dei volumi.

---

File creati/modificati in questa repo per risolvere un problema noto con la CLI di Odoo:
- `config/odoo.conf` (aggiunto) - sposta `admin_passwd` nel file di configurazione invece che passarlo come flag CLI non supportato.

Se vuoi, posso mostrarti i comandi PowerShell esatti per il debug o applicare altre migliorie (es. template per variabili d'ambiente).
