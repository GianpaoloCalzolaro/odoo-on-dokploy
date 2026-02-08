# Immagine ufficiale Odoo 18 basata su Debian Bookworm
FROM odoo:18.0

# Passiamo all'utente root per installare dipendenze e gestire file di sistema
USER root

# Pulizia preventiva e installazione dipendenze di sistema
# Nota: Abbiamo separato i comandi per chiarezza e per facilitare il debug del log
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    libffi-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiamo il file delle dipendenze Python (requirements.txt deve essere nella root del repo)
COPY ./requirements.txt /opt/odoo/requirements.txt

# Installazione delle dipendenze Python richieste dagli add-on
RUN pip install --no-cache-dir -r /opt/odoo/requirements.txt

# Creazione della cartella per gli add-on custom (se non esiste)
# Copiamo il contenuto della cartella addons locale nel container
COPY ./addons /mnt/extra-addons

# Copia del file di configurazione odoo.conf
COPY ./config/odoo.conf /etc/odoo/odoo.conf

# Gestione cruciale dei permessi: l'utente 'odoo' deve possedere i file per caricarli
RUN chown -R odoo:odoo /mnt/extra-addons /etc/odoo/odoo.conf /var/lib/odoo

# Torniamo all'utente non privilegiato per l'esecuzione
USER odoo