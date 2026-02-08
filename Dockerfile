# Use the official Odoo 18 image as base
FROM odoo:18.0

# Switch to root to install system dependencies and pip packages
USER root

# Install system dependencies that might be required by OCA modules or custom addons
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpq-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
# This is done before copying code to leverage Docker cache
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Create directory for custom addons and copy them
# We copy them to /mnt/extra-addons which is a standard Odoo path
COPY ./addons /mnt/extra-addons

# Copy the configuration file to the standard location
COPY ./config/odoo.conf /etc/odoo/odoo.conf

# Set correct permissions so the 'odoo' user can read the files
RUN chown -R odoo:odoo /mnt/extra-addons /etc/odoo/odoo.conf

# Switch back to the non-privileged odoo user
USER odoo