import paramiko, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('85.239.237.53', username='root', password='Lu7chLT38HSbcNndP7WA', timeout=15)

def run(cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    return out, err

def print_cmd(cmd, timeout=120):
    out, err = run(cmd, timeout)
    print(f'$ {cmd}')
    if out: print(out[:2000])
    if err and 'error' in err.lower(): print(f'[ERR] {err[:300]}')
    print('---')

# ══════════════════════════════════════════════
# PHASE 1: DEEP ANALYSIS OF SERVER STATE
# ══════════════════════════════════════════════
print('╔══════════════════════════════════════════╗')
print('║  PHASE 1: ANALYZING SERVER STATE        ║')
print('╚══════════════════════════════════════════╝')

print('\n── 1.1 Running Containers ──')
print_cmd('docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"')

print('\n── 1.2 Docker Images ──')
print_cmd('docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"')

print('\n── 1.3 Disk Usage ──')
print_cmd('docker system df')

print('\n── 1.4 Server Code Structure ──')
print_cmd('ls -la /root/leadforge/')
print_cmd('ls -la /root/leadforge/backend/app/')
print_cmd('ls -la /root/leadforge/frontend/src/ 2>/dev/null || echo "no frontend src"')

print('\n── 1.5 .env File ──')
out, _ = run('cat /root/leadforge/.env')
print(out)

print('\n── 1.6 Nginx Config ──')
print_cmd('cat /etc/nginx/sites-available/hyperclients')
print_cmd('ls -la /etc/nginx/sites-enabled/')

print('\n── 1.7 Git Status on Server ──')
print_cmd('cd /root/leadforge && git log --oneline -5')
print_cmd('cd /root/leadforge && git status --short')

print('\n── 1.8 Docker Compose Config on Server ──')
print_cmd('cat /root/leadforge/docker-compose.yml')

print('\n── 1.9 Check if Ports are in use ──')
print_cmd('ss -tlnp | grep -E ":(8000|3000|80) "')

print('\n── 1.10 Old leadforge files from prev deploy? ──')
print_cmd('find /root -name "*.yml" -not -path "*/go/*" 2>/dev/null | head -10')

# ══════════════════════════════════════════════
# PHASE 2: CLEAN DEPLOYMENT
# ══════════════════════════════════════════════
print('\n╔══════════════════════════════════════════╗')
print('║  PHASE 2: CLEAN DEPLOYMENT              ║')
print('╚══════════════════════════════════════════╝')

# Kill any old containers
print('\n── 2.1 Cleaning old containers ──')
run('docker compose -f /root/leadforge/docker-compose.yml down 2>&1', 60)
run('docker rm -f $(docker ps -aq) 2>/dev/null')
print('Done cleaning')

# Ensure code is fresh from GitHub
print('\n── 2.2 Pulling latest code ──')
out, err = run('cd /root/leadforge && git fetch origin 2>&1')
print(out[:200])
out, err = run('cd /root/leadforge && git reset --hard origin/main 2>&1')
print(out[:200])
print(f'Now at: {run("cd /root/leadforge && git log --oneline -1")[0]}')

# Restore .env (was lost during git reset)
print('\n── 2.3 Re-creating .env ──')
env_content = '''SUPABASE_URL=https://wtradahkkpbkbhmkkpal.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0cmFkYWhra3Bia2JobWtrcGFsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwMDcyNjcsImV4cCI6MjA5NjU4MzI2N30.erQe6RS6nAog2inQQdDiwWLe4yAutq_70eKdcGnTDg
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0cmFkYWhra3Bia2JobWtrcGFsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTAwNzI2NywiZXhwIjoyMDk2NTgzMjY3fQ.QUKn8jhwCSyT1mnsMIq4dhPZND7xzG5VWxO5heO4fJI
GEMINI_API_KEY=AIzaSyD4QpgqJ-9UTpB5nHfGuKSEKOzEJpsG5Ao
GMAPS_SCRAPER_PATH=/app/google-maps-scraper/google-maps-scraper
FRONTEND_URL=http://85.239.237.53
BACKEND_URL=http://localhost:8000
ENVIRONMENT=production
'''
run(f'cat > /root/leadforge/.env << \'ENVEOF\'\n{env_content}\nENVEOF')

# Fix Dockerfile Go version to latest
print('\n── 2.4 Fixing Dockerfile Go version ──')
run('sed -i "s/golang:1\.23-bookworm/golang:latest/g" /root/leadforge/backend/Dockerfile')
run('sed -i "s/golang:1\.24-bookworm/golang:latest/g" /root/leadforge/backend/Dockerfile')
out, _ = run('head -8 /root/leadforge/backend/Dockerfile')
print(out)

# Build backend (frontend will be built by compose)
print('\n── 2.5 Building backend image ──')
out, err = run('cd /root/leadforge && docker compose build --no-cache backend 2>&1', 600)
combined = out + err
if 'error' in combined.lower() and 'failed' in combined.lower():
    print('[ERROR] Build failed:')
    print(combined[-800:])
else:
    print('Backend build OK')
    # Verify image
    img, _ = run('docker images leadforge-backend --format "{{.Size}}"')
    print(f'  Image size: {img}')

# Build frontend separately too
print('\n── 2.6 Building frontend image ──')
out, err = run('cd /root/leadforge && docker compose build --no-cache frontend 2>&1', 600)
combined = out + err
if 'error' in combined.lower() and 'failed' in combined.lower():
    print('[ERROR] Frontend build failed:')
    print(combined[-800:])
else:
    print('Frontend build OK')
    img, _ = run('docker images leadforge-frontend --format "{{.Size}}"')
    print(f'  Image size: {img}')

# Start containers
print('\n── 2.7 Starting containers ──')
out, err = run('cd /root/leadforge && docker compose up -d 2>&1', 60)
print(out[:500])
if err: print(f'[ERR] {err[:300]}')

# Wait for services to start
import time
print('\n── 2.8 Waiting for services (15s) ──')
time.sleep(15)

# Check status
print('\n── 2.9 Container Status ──')
out, _ = run('docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"')
print(out)

# Logs if failed
print('\n── 2.10 Container Logs (if any issues) ──')
out, _ = run('docker compose -f /root/leadforge/docker-compose.yml logs --tail=30 2>&1')
if 'Error' in out or 'error' in out:
    print(out[:2000])
else:
    print('No errors in logs')

# ══════════════════════════════════════════════
# PHASE 3: HEALTH CHECKS
# ══════════════════════════════════════════════
print('\n╔══════════════════════════════════════════╗')
print('║  PHASE 3: HEALTH CHECKS                 ║')
print('╚══════════════════════════════════════════╝')

print('\n── 3.1 Backend Health ──')
be, _ = run('curl -s http://localhost:8000/api/health')
print(be[:200])

print('\n── 3.2 Frontend Health ──')
fe, _ = run('curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/')
print(f'HTTP {fe}')

print('\n── 3.3 Nginx (public URL) ──')
ng, _ = run('curl -s -o /dev/null -w "%{http_code}" http://85.239.237.53/')
print(f'HTTP {ng}')
ng_api, _ = run('curl -s -o /dev/null -w "%{http_code}" http://85.239.237.53/api/health')
print(f'API via nginx: HTTP {ng_api}')

# ── Verify nginx config is working ──
print('\n── 3.4 Nginx config test ──')
out, _ = run('nginx -t 2>&1')
print(out)

client.close()

url = 'http://85.239.237.53'
print(f'\n{"═"*50}')
print(f'  ANALYSIS & DEPLOYMENT COMPLETE')
print(f'  URL: {url}')
print(f'  API: {url}/api/health')
print(f'  Dashboard: {url}/dashboard')
print(f'{"═"*50}')
