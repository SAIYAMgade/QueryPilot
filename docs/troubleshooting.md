# QueryPilot Troubleshooting Guide

This guide covers common issues encountered when connecting to Oracle Database or running QueryPilot locally.

---

## 1. Oracle Connection Issues

### ORA-12541: TNS:no listener
- **Cause**: Oracle Database listener is not running or port 1521 is not accessible.
- **Check**: Verify if the Oracle container is running:
  ```bash
  docker ps
  ```
- **Fix**: Start the Oracle container:
  ```bash
  docker run -d --name oracle23ai -p 1521:1521 -e ORACLE_PWD=oracle_password container-registry.oracle.com/database/free:latest
  ```

### ORA-01017: invalid username/password; logon denied
- **Cause**: Incorrect database credentials in `.env`.
- **Fix**: Verify `ORACLE_USER` and `ORACLE_PASSWORD` match the schema user configured in Oracle Database. Default demo user: `qp_app_user` / `qp_app_password`.

### ORA-12514: TNS:listener does not currently know of service requested
- **Cause**: Oracle pluggable database (PDB) is not yet open or service name is incorrect.
- **Fix**: In Oracle Database Free, the default pluggable database service is `FREEPDB1`. Check PDB status:
  ```sql
  ALTER PLUGGABLE DATABASE freepdb1 OPEN;
  ```

---

## 2. Docker & WSL2 Environment Limitations

If Docker Desktop encounters WSL2 errors on Windows (`Wsl/Service/E_UNEXPECTED`):
- **QueryPilot Behavior**: QueryPilot automatically activates its **Deterministic Offline Simulation Sandbox**!
- You can explore the full UI, execute queries against the Retail schema, generate realistic execution plans, run query comparisons, diagnose ORA- errors, and generate investigation reports without crashing.
- Notice banner in the top header will explicitly indicate `Offline Simulation Sandbox (Oracle at localhost:1521 unreachable)` to maintain complete transparency.
