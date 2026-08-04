# Scripts Directory - PickerWheel v2 (PostgreSQL)

This directory contains scripts for managing the PickerWheel Contest System with PostgreSQL backend.

## 🚀 Quick Start

### macOS / Linux
```bash
# Start the system
./scripts/docker.sh start

# Check status
./scripts/docker.sh status

# Run data migration (first time only)
./scripts/docker.sh migrate

# View logs
./scripts/docker.sh logs
```

### Windows
```batch
:: Use the interactive menu
scripts\docker-menu.bat

:: Or individual scripts
scripts\start-pickerwheel.bat
scripts\stop-pickerwheel.bat
scripts\restart-pickerwheel.bat
```

## 📋 Script Reference

### Docker Management (macOS/Linux) - `docker.sh`

```bash
./scripts/docker.sh [command]
```

| Command | Description |
|---------|-------------|
| `start` | Start PostgreSQL + PickerWheel containers |
| `stop` | Stop all containers |
| `restart` | Restart all containers |
| `status` | Show container and health status |
| `logs` | Show application logs (follow) |
| `db-logs` | Show PostgreSQL logs |
| `migrate` | Run data migration from itemlist_dates_v2.txt |
| `shell` | Open bash shell in app container |
| `db-shell` | Open PostgreSQL shell |
| `info` | Show system information |
| `test` | Test all API endpoints |
| `clean` | Remove containers and volumes (CAUTION!) |
| `legacy` | Use legacy SQLite backend |
| `help` | Show help message |

### Windows Scripts

| Script | Description |
|--------|-------------|
| `docker-menu.bat` | Interactive menu for all operations |
| `start-pickerwheel.bat` | Start containers |
| `stop-pickerwheel.bat` | Stop containers |
| `restart-pickerwheel.bat` | Restart containers |

## 🔧 Configuration

### Ports

| Version | Port | Description |
|---------|------|-------------|
| v2 (PostgreSQL) | 9080 | Main application |
| v2 (PostgreSQL) | 5432 | PostgreSQL database |
| Legacy (SQLite) | 8082 | Legacy application |

### Access URLs

- **Main Wheel**: http://localhost:9080
- **Admin Panel**: http://localhost:9080/admin
- **Admin Password**: `myTAdmin2025`

### Key Files

| File | Description |
|------|-------------|
| `itemlist_dates_v2.txt` | Prize configuration file |
| `docker-compose.yml` | PostgreSQL Docker configuration |
| `docker-compose.yml` | Legacy Docker configuration |

## 🗃️ Database Commands

### Access PostgreSQL Shell
```bash
# macOS/Linux
./scripts/docker.sh db-shell

# Windows (from menu)
# Option 5: Open Database Shell
```

### Common SQL Queries
```sql
-- View all prizes
SELECT id, name, is_enabled, display_order FROM prizes;

-- View available prizes for today
SELECT p.name, i.remaining_quantity 
FROM prizes p 
JOIN prize_inventory i ON p.id = i.prize_id 
WHERE i.available_date = CURRENT_DATE 
AND p.is_enabled = TRUE;

-- View recent transactions
SELECT * FROM transactions ORDER BY created_at DESC LIMIT 10;

-- View statistics
SELECT category_id, COUNT(*) as wins 
FROM transactions 
WHERE created_at::date = CURRENT_DATE 
GROUP BY category_id;
```

## 🔄 Data Migration

First-time setup requires migrating data from `itemlist_dates_v2.txt`:

```bash
# macOS/Linux
./scripts/docker.sh migrate

# Windows (from menu)
# Option 4: Run Data Migration
```

## 🧪 Testing

### Test API Endpoints
```bash
# macOS/Linux
./scripts/docker.sh test

# Windows (from menu)
# Option 9: Test API Endpoints
```

### Manual API Tests
```bash
# Health check
curl http://localhost:9080/api/health

# Get wheel display prizes
curl http://localhost:9080/api/prizes/wheel-display

# Get available prizes
curl http://localhost:9080/api/prizes/available

# Get statistics
curl http://localhost:9080/api/stats
```

## 🚨 Troubleshooting

### Container won't start
```bash
# Check Docker is running
docker info

# View startup logs
./scripts/docker.sh logs

# Restart containers
./scripts/docker.sh restart
```

### Database connection errors
```bash
# Check PostgreSQL is healthy
docker exec pickerwheel-db pg_isready -U pickerwheel -d pickerwheel

# View database logs
./scripts/docker.sh db-logs
```

### Reset everything
```bash
# WARNING: This removes all data!
./scripts/docker.sh clean
./scripts/docker.sh start
./scripts/docker.sh migrate
```

## 📦 Legacy Mode

To use the old SQLite backend:

```bash
# macOS/Linux
./scripts/docker.sh legacy start
./scripts/docker.sh legacy stop

# Windows (from menu)
# Option L: Use Legacy Backend
```

Legacy backend runs on port 8082.

## 📝 Data Validation Scripts

### Validation Suite
```bash
./scripts/run_validation_suite.sh
./scripts/validation_suite_curl.sh
```

### Prize Updates
```bash
python3 scripts/validate_and_update_prizes.py
python3 scripts/verify_admin_data.py
python3 scripts/update_csvs_from_v2.py
```

## 📞 Support

1. Check status: `./scripts/docker.sh status`
2. View logs: `./scripts/docker.sh logs`
3. Test system: `./scripts/docker.sh test`
4. Check README: `../README-v2.md`
