# KICKNEXA Database Starter

Files:
- `kicknexa.db` — SQLite database ready for development/testing.
- `schema.sql` — schema notes.
- `README.md` — this guide.

Core entities:
- Users
- Athletes
- Organizations
- Opportunities
- Athlete applications/saved opportunities
- Sports
- Verification documents

The demo rows are clearly labeled and contain no real personal information.

## Production recommendation
For a live public platform, move to PostgreSQL or another managed database, use a real authentication system with secure password hashing, encrypted transport, access controls, backups, audit logs, and a privacy/consent system. Do not store passwords in plaintext. For minors, implement an appropriate guardian-consent workflow before publishing personal athlete data.
