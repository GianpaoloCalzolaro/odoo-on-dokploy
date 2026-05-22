# Checklist pre-deploy

Lista di controllo obbligatoria per ogni nuovo progetto cliente prima di procedere con il deploy.

## Configurazione variabili d'ambiente

- [ ] `PROJECT_NAME` compilato e **univoco** rispetto ad altre istanze attive sul nodo
- [ ] `COMPOSE_PROJECT_NAME` corrisponde a `PROJECT_NAME`
- [ ] `DOMAIN` punta correttamente al nodo Dokploy (record DNS configurato e propagato)
- [ ] `POSTGRES_PASSWORD` cambiata dal valore placeholder `CAMBIA_QUESTA_PASSWORD`
- [ ] `ODOO_ADMIN_PASSWD` cambiata dal valore placeholder `CAMBIA_QUESTA_PASSWORD`
- [ ] `ODOO_IMAGE` punta all'immagine corretta del progetto (`ghcr.io/<owner>/odoo18-[nomecliente]:latest`)

## Infrastruttura

- [ ] Package GHCR visibile e accessibile (verifica visibilità pubblica o permessi corretti)
- [ ] Rete `dokploy-network` presente sul nodo (`docker network ls | grep dokploy-network`)
- [ ] Traefik in esecuzione e connesso alla rete `dokploy-network`
- [ ] Porte 80 e 443 aperte sull'host (necessarie per Let's Encrypt / ACME)

## CI/CD e deploy

- [ ] Prima build CI/CD completata con successo (GitHub Actions → Build and Push to GHCR)
- [ ] Immagine pubblicata su GHCR con il tag `:latest` corretto
- [ ] Progetto configurato su Dokploy con le stesse variabili d'ambiente del `.env`
- [ ] Deploy su Dokploy completato senza errori

## Verifica finale

- [ ] Accesso HTTPS verificato nel browser (`https://<DOMAIN>`)
- [ ] Certificato TLS (Let's Encrypt) valido e attivo
- [ ] Login Odoo funzionante con le credenziali configurate
- [ ] Nessun errore critico nei log: `docker compose logs odoo`
