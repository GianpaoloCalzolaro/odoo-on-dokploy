#!/bin/sh
set -eu

envsubst < /etc/odoo/odoo.conf.template > /etc/odoo/odoo.conf

exec /entrypoint.sh "$@"
