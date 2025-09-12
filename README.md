# odoo-on-dokploy

Odoo deployment setup for Dokploy with custom addons.

## Structure

```
odoo-on-dokploy/
├─ docker-compose.yml    # Docker Compose configuration
├─ .env                  # Environment variables
├─ addons/              # Custom Odoo modules
│  ├─ mio_modulo_a/     # Custom module A
│  └─ mio_modulo_b/     # Custom module B
```

## Usage

1. Start the services:
   ```bash
   docker compose up -d
   ```

2. Access Odoo at: http://localhost:8069

3. Default credentials:
   - Database: odoo
   - Email: admin
   - Password: admin123

## Custom Modules

Place your custom Odoo modules in the `addons/` directory. They will be automatically available in Odoo.

## Environment Variables

Edit the `.env` file to customize:
- `POSTGRES_DB`: Database name
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `ODOO_ADMIN_PASSWD`: Odoo master password
