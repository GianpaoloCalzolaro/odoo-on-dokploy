FROM odoo:18.0

USER root

# Copy custom add-ons from the repository into the image
COPY ./addons /mnt/extra-addons

# Copy the existing Odoo configuration and update addons_path
# to point to /mnt/extra-addons (matching the COPY destination above)
COPY ./config/odoo.conf /etc/odoo/odoo.conf
RUN sed -i 's|/mnt/addons|/mnt/extra-addons|g' /etc/odoo/odoo.conf

# Set correct ownership
RUN chown -R odoo:odoo /mnt/extra-addons \
    && chown odoo:odoo /etc/odoo/odoo.conf

USER odoo
