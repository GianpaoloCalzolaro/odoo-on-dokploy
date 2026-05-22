# odoo-on-dokploy

Template GitHub per avviare una nuova istanza Odoo 18 su [Dokploy](https://dokploy.com/) con Docker Compose, Traefik e CI/CD automatizzata via GitHub Actions.

> Consulta [`CHECKLIST.md`](CHECKLIST.md) prima di ogni nuovo deploy.

## Struttura del repository

```
odoo-on-dokploy/
├── .env.example          # Variabili d'ambiente da copiare in .env
├── .github/
│   └── workflows/
│       └── build-and-push-ghcr.yml  # CI/CD: build e push immagine su GHCR
├── addons/               # Moduli Odoo custom del progetto
├── config/
│   └── odoo.conf         # Template di configurazione Odoo (renderizzato a runtime)
├── docker/
│   └── entrypoint.sh     # Wrapper entrypoint: esegue envsubst poi avvia Odoo
├── docker-compose.yml    # Stack: odoo + postgres + rete Traefik
├── Dockerfile            # Immagine custom basata su odoo:18.0
└── requirements.txt      # Dipendenze Python aggiuntive (installate nel Dockerfile)
```

---

## 1. Avviare un nuovo progetto

### 1.1 Creare il repository dal template

1. Aprire [https://github.com/GianpaoloCalzolaro/odoo-on-dokploy](https://github.com/GianpaoloCalzolaro/odoo-on-dokploy)
2. Cliccare **Use this template → Create a new repository**
3. Nominare il repository con la convenzione `odoo18-[nomecliente]` (es. `odoo18-acme`)

> Il nome del repository diventa parte del tag Docker pubblicato su GHCR:
> `ghcr.io/<owner>/odoo18-[nomecliente]:latest`

### 1.2 Clonare e configurare le variabili

```bash
git clone https://github.com/<owner>/odoo18-[nomecliente].git
cd odoo18-[nomecliente]
cp .env.example .env
```

Aprire `.env` e compilare **tutte** le variabili:

| Variabile | Esempio | Note |
|---|---|---|
| `PROJECT_NAME` | `acme` | Univoco sul nodo; usato per router Traefik e nomi volumi |
| `COMPOSE_PROJECT_NAME` | `acme` | Deve corrispondere a `PROJECT_NAME` |
| `DOMAIN` | `odoo.acme.it` | DNS già puntato al nodo Dokploy |
| `ODOO_IMAGE` | `ghcr.io/<owner>/odoo18-acme:latest` | Immagine pubblicata dalla CI/CD |
| `POSTGRES_DB` | `odoo` | Nome del database |
| `POSTGRES_USER` | `odoo` | Utente PostgreSQL |
| `POSTGRES_PASSWORD` | *(stringa sicura)* | **Cambiare** dal placeholder |
| `ODOO_ADMIN_PASSWD` | *(stringa sicura)* | **Cambiare** dal placeholder |
| `ODOO_VERSION` | `18.0` | Versione Odoo |
| `POSTGRES_VERSION` | `16` | Versione PostgreSQL |

### 1.3 Prima build CI/CD

```bash
git push origin main
```

La GitHub Action `.github/workflows/build-and-push-ghcr.yml` si attiva automaticamente su push verso `main` quando vengono modificati `Dockerfile`, `addons/`, `config/` o `requirements.txt`. Al termine pubblica l'immagine su GHCR.

Verificare che il package GHCR sia visibile e accessibile (pubblico o con i permessi corretti).

### 1.4 Configurare il progetto su Dokploy

1. Creare un nuovo progetto su Dokploy (tipo **Docker Compose**)
2. Collegare il repository GitHub appena creato
3. Nella sezione **Environment Variables** di Dokploy inserire le stesse variabili presenti nel `.env` locale
4. Impostare il branch di deploy su `main`

### 1.5 Creare la rete Docker sul nodo

Se la rete `dokploy-network` non esiste ancora sul nodo:

```bash
docker network create dokploy-network
```

Verificare con:

```bash
docker network ls | grep dokploy-network
```

### 1.6 Verificare il deploy

Dopo il deploy, aprire `https://<DOMAIN>` nel browser e controllare che:

- La pagina di login Odoo sia raggiungibile via HTTPS
- Il certificato TLS (Let's Encrypt) sia valido
- Non ci siano errori nei log: `docker compose logs -f odoo`

---

## 2. Aggiungere moduli custom

### 2.1 Struttura della cartella `addons/`

Ogni modulo Odoo è una sottocartella con il file `__manifest__.py`:

```
addons/
├── mail_debrand/             # Modulo baseline: rimozione branding email
├── web_chatter_position/     # Modulo baseline: posizione chatter configurabile
├── website_odoo_debranding/  # Modulo baseline: rimozione "Powered by Odoo"
└── mio_modulo_custom/        # Modulo custom del progetto
    ├── __init__.py
    ├── __manifest__.py
    └── ...
```

I moduli nella cartella `addons/` vengono copiati nel container al momento della build (`COPY ./addons /mnt/extra-addons`) e sono disponibili come **extra-addons** in Odoo.

### 2.2 Convenzioni di naming

- Usare `snake_case` per il nome della cartella/modulo (es. `crm_custom_acme`)
- Il nome della cartella deve corrispondere al valore `name` nel `__manifest__.py`
- Prefissare i moduli specifici del cliente con il nome del progetto per evitare conflitti (es. `acme_sale_custom`)

### 2.3 Dipendenze Python aggiuntive

Se un modulo custom richiede librerie Python non incluse nell'immagine base Odoo:

1. Aggiungere le dipendenze nel file **`requirements.txt`** nella root del repository (installate a livello di immagine):

   ```
   pandas
   requests
   ```

2. Oppure creare un `requirements.txt` all'interno della cartella del modulo custom. Il `Dockerfile` lo rileva e lo installa automaticamente:

   ```dockerfile
   find /mnt/extra-addons -name 'requirements.txt' \
       -exec pip install --no-cache-dir --break-system-packages -r {} \;
   ```

Dopo ogni modifica a `requirements.txt` o ai file del modulo, fare push su `main` per triggerare una nuova build CI/CD.

---

## 3. Operazioni di manutenzione

### 3.1 Backup del database

Eseguire un dump PostgreSQL dal container `db`:

```bash
docker exec <PROJECT_NAME>-db-1 pg_dump -U odoo -d odoo -F c -f /tmp/odoo_backup.dump
docker cp <PROJECT_NAME>-db-1:/tmp/odoo_backup.dump ./odoo_backup_$(date +%Y%m%d).dump
```

Per includere i filestore di Odoo (allegati, immagini):

```bash
docker cp <PROJECT_NAME>-odoo-1:/var/lib/odoo ./odoo_filestore_$(date +%Y%m%d)
```

### 3.2 Aggiornamento dell'immagine

Per aggiornare l'immagine Odoo all'ultima versione pubblicata dalla CI/CD:

```bash
docker compose pull odoo
docker compose up -d odoo
```

Su Dokploy è sufficiente cliccare **Redeploy** per scaricare l'ultima immagine da GHCR.

### 3.3 Restore su nuovo nodo

1. Copiare il file di backup `.dump` sul nuovo nodo
2. Creare la rete `dokploy-network` se non esiste: `docker network create dokploy-network`
3. Avviare solo il servizio database: `docker compose up -d db`
4. Ripristinare il dump:

   ```bash
   docker cp odoo_backup.dump <PROJECT_NAME>-db-1:/tmp/
   docker exec <PROJECT_NAME>-db-1 pg_restore -U odoo -d odoo --clean /tmp/odoo_backup.dump
   ```

5. Ripristinare il filestore nella cartella del volume `odoo-data`:

   ```bash
   docker cp ./odoo_filestore/. <PROJECT_NAME>-odoo-1:/var/lib/odoo/
   ```

6. Avviare il servizio Odoo: `docker compose up -d odoo`

---

## Debug rapido

```bash
docker compose ps                          # stato dei container
docker compose logs -f odoo               # log Odoo in tempo reale
docker network inspect dokploy-network    # verifica connessione Traefik ↔ Odoo
docker compose exec odoo bash             # shell nel container Odoo
```
