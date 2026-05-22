#!/bin/sh
set -eu

: "${ODOO_ADMIN_PASSWD:?ODOO_ADMIN_PASSWD must be set}"
: "${POSTGRES_DB:?POSTGRES_DB must be set}"
: "${POSTGRES_USER:?POSTGRES_USER must be set}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}"

envsubst < /etc/odoo/odoo.conf.template > /etc/odoo/odoo.conf

exec /entrypoint.sh "$@"
