# Electric SQL

This research was technically done for FMTM, but will be used in Drone TM most likely too.

## Local First - the future of state

- The diagram below shows the evoluation of state transfer in web apps over time.

![Image](./evolution_of_state.png)

- The Local-First approach essentially:
  - Manages all state on the **frontend**, giving near instant responsiveness.
  - Frontend state is stored in a database, likely via WASM module (SQLite, PGLite).
  - The state is synced continually with a layers that sits between the app and the DB.
  - Conflicts are handled by CRDT, avoiding integrity errors.

This allows for apps that can:
- Run entirely offline, then sync when online.
- Allow for real-time data loading on the frontend - i.e. two-way sync.
- Very responsive applications, with minimal API calls required.

## Testing Setup

### DB Logical Replication

Enable logical replication on your postgres instance, e.g. in compose:

```yaml
services:
  db:
    ...
    command: -c 'max_connections=300' -c 'wal_level=logical'
```

> max_connections is not required, it's just for demonstration of two config vars.

### Run Electric Service Layer

Add the `electric` service to your docker-compose file:

```yaml
  electric:
    image: "electricsql/electric:${ELECTRIC_TAG:-0.12.1}"
    depends_on:
      fmtm-db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://${FMTM_DB_USER:-fmtm}:${FMTM_DB_PASSWORD:-fmtm}@${FMTM_DB_HOST:-fmtm-db}/${FMTM_DB_NAME:-fmtm}
      DATABASE_REQUIRE_SSL: false
      ELECTRIC_WRITE_TO_PG_MODE: direct_writes
      PG_PROXY_PASSWORD: proxy_password
      AUTH_MODE: insecure
    ports:
      - "5133:5133"
      - "65432:65432"
    networks:
      - fmtm-net
    restart: "unless-stopped"
```

- The env vars here are configured for insecure mode (not production).
- Ports `5133` and `65432` must also be exposed.

### Enable Electric On Your Database

- This step was missing from the docs.
- Extracting the schemas below will fail if ELECTRIC is not enabled for a table.
- First connect to your database via the Electric database proxy:

```bash
psql -h localhost -p 65432 -U fmtm`
```

Then run the SQL:

```sql
ALTER TABLE task_history
  ENABLE ELECTRIC;

ELECTRIC GRANT ALL
  ON items
  TO ANYONE;
```

Important notes:
- There are many limitations documented for supported datatypes.
- Electric does not support auto-incrementing primary keys (SERIAL).
- It also does not support DEFAULT values, or PostGIS types.
- Ensure the table is stripped down to the bare minimum required.
- The access control is also not fully implemented, so the `GRANT ALL`
  command may not be required.

### Add TypeScript models

Install electric-sql package:

```bash
npm install electric-sql
```

Generate the schemas once with: `npx electric-sql generate`

Or generate on every build with:

```json
"scripts": {
  "prebuild": "npx electric-sql generate"
}
```

This typically connects to the `electric` service running on `localhost`
(via the exposed ports).

For my setup, I have my IDE in a container... so I had to work around:

```bash
npx electric-sql generate --service http://electric:5133 --proxy postgresql://fmtm:proxy_password@electric:65432/fmtm
```

The `prisma` schemas/models will be generated in your frontend `src` folder.
These are required and should be committed to your repo.

> Note: if using `pnpm` to do this, you may get errors. Both `prisma` and `zod`
> must be manually installed as dependencies. This is not an issue with `npm`.

### Use the models

First create a dummy JWT for the insecure connection (mandatory):

- Go to https://token.dev
- Remove all claims other than `sub`.
- Copy the JWT for later.

Create a module to init the frontend connection:

```js
import { electrify } from 'electric-sql/pglite';
import { PGlite } from '@electric-sql/pglite';
import { type Electric, schema } from '../generated/client';

const config = {
  url: 'http://localhost:5133'
};

export const initElectric = async (): Promise<Electric> => {
  const conn = new PGlite('idb://fmtm.db', {
    relaxedDurability: true,
  });
  const electric = await electrify(conn, schema, config);
  await electric.connect('THE_TOKEN_YOU_GENERATED');
  return electric;
};
```

> This uses a `pglite` database via indexeddb in the browser.

Now the next steps will not be documented, but here is the gist:
- The concept of Shapes are used as a subset of a table to sync to the frontend db.
- The shapes interact with the Prisma models and are where you add, update, delete data.
  The data is synced with the database if you are online, or simply stored for later sync
  if you are offline.
- To have two-way real-time sync, you must configure reactive variables: this is easy for
  now with React, but Svelte integration isn't there. I added wrapper to handle this in 
  FMTM.
- Now you should be able to:
  - Interact with data in the frontend db, and sync at internval.
  - Enable two-way sync via reactive components.
