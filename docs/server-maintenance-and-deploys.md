# Server maintenance and Deploys

The deploy process is currently pretty manual.

- Test stuff locally first. "Testing" in this case involves clicking around,
  creating new entries, deleting them, and generally manually trying to break
  it.

- Push it to staging, and try again to break it.

  ```bash
  git push staging yourbranch:master
  ```

- If that all looks good, deploy to production! Traffic is generally very low
  at night in the US. People could be notified on Zulip about downtime, but
  weight it against the spam cost of notifying people of downtime they will
  never experience.

    ```bash
    git push heroku master:master
    ```

## Rules of thumb

- Avoid pushing things that may break.
- QA really hard, before anything goes out.

Users' trust is a hard earned thing. Safeguard it!

# Staging environment

To develop and test features, we have a staging environment at
`blaggregator-staging`

Instructions for configuring git locally:
https://devcenter.heroku.com/articles/multiple-environments

It's got a partial copy of the production database.  It can be
manually [updated manually](DB-dump.md). Heroku lets you do
[db-to-db copies](https://devcenter.heroku.com/articles/heroku-postgres-backups#direct-database-to-database-copies)

It **doesn't** have Zulip keys, so no worries about accidents there.

It has an env var STAGING which determines some things in settings.py (mostly
which DB and S3 bucket to use)

# Heroku Database backups

Blaggregator is hosted on Heroku and here is how to get the latest db dump

## Download backup

Create new backup and download it.

```bash
$ heroku pg:backups public-url --app blaggregator
$ curl -o latest.dump `heroku pg:backups public-url --app blaggregator`
```

## Restore backup (locally)

Loads the dump into your local database using the pg_restore tool.

```bash
$ pg_restore --verbose --clean --no-acl --no-owner -h localhost -U sasha -d blaggregator_dev latest.dump
```

## Restore backup on heroku (staging)

```bash
$ heroku pg:backups public-url --app blaggregator   # Get backup url
$ heroku pg:backups restore $BACKUP_URL DATABSE_URL  # $BACKUP_URL is obtained above
```
