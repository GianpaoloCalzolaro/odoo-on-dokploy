# Immagine ufficiale Odoo 18 basata su Debian Bookworm
FROM odoo:18.0

# Passiamo all'utente root per installare dipendenze e gestire file di sistema
USER root

# Copiamo requirements e addons prima dell'installazione per sfruttare la cache dei layer
COPY ./requirements.txt /opt/odoo/requirements.txt
COPY ./addons /mnt/extra-addons

# Installazione dipendenze di sistema (build-time), dipendenze Python, e pulizia
# in un singolo layer per minimizzare le dimensioni dell'immagine finale
# hadolint ignore=DL3008
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
    && pip install --no-cache-dir --break-system-packages \
        -r /opt/odoo/requirements.txt \
    && find /mnt/extra-addons -name 'requirements.txt' \
        -exec pip install --no-cache-dir --break-system-packages -r {} \; \
    && apt-get purge -y --auto-remove \
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

# Copia del file di configurazione odoo.conf
COPY ./config/odoo.conf /etc/odoo/odoo.conf

# Gestione cruciale dei permessi: l'utente 'odoo' deve possedere i file per caricarli
RUN chown -R odoo:odoo /mnt/extra-addons /etc/odoo/odoo.conf /var/lib/odoo

# Torniamo all'utente non privilegiato per l'esecuzione
USER odoo

# Healthcheck: verifica che Odoo risponda sulla porta 8069
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8069/web/health')" || exit 1