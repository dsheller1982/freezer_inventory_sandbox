# Freezer Inventory Sandbox

A disposable, full-CRUD portfolio demonstration built with Streamlit, Python, and MySQL/MariaDB.
It contains synthetic freezer data only and has no connection to the private household deployment.

## Features

- Browse and search inventory by item, category, or location.
- Add new items, restock existing items, and remove inventory.
- Record every write with before/after quantities in a transaction history.
- Display durable success confirmations after Streamlit reruns.
- Restore synthetic baseline data manually or from a scheduled job.
- Keep database writes atomic with row locks and transactions.

## Run locally with Docker

```bash
docker compose up --build
```

Open <http://localhost:8501>. The local credentials in `docker-compose.yml` are intentionally
demo-only and must never be reused for a public deployment.

To reset the local demo:

```bash
docker compose exec app python -m scripts.reset_demo
```

## Railway deployment layout

Use one Railway project containing three services:

1. **MySQL database** — provision Railway's MySQL service.
2. **Streamlit app** — deploy this repository using its Dockerfile.
3. **Reset cron service** — deploy the same repository, set its start command to
   `python -m scripts.reset_demo`, and schedule it for `0 */6 * * *` (every six hours, UTC).

For both code services, reference the database service's variables rather than copying real
credentials into the repository. The application supports Railway's standard `MYSQLHOST`,
`MYSQLPORT`, `MYSQLDATABASE`, `MYSQLUSER`, and `MYSQLPASSWORD` variables automatically.

The container initializes missing tables automatically without overwriting existing demo changes.
To initialize manually, run:

```bash
python -m scripts.init_database
```

Generate a Railway domain for the Streamlit service first. Add a custom domain only after the
generated domain is healthy. Do not create a public TCP proxy for the MySQL service; the app and
reset service should reach it over Railway's private network.

## Original project cleanup represented here

The private schema export contained an active `freezer_inventory` table, two legacy/backup tables,
and an unused `Column1`. This public schema intentionally carries forward only the fields used by
the active Streamlit application and adds `inventory_transactions` for its audit trail.
