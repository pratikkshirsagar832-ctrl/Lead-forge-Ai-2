import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

host = '85.239.237.53'
password = 'Lu7chLT38HSbcNndP7WA'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(host, username='root', password=password, timeout=15)

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return out.strip(), err.strip()

# Step 1: Install Docker
print('=== STEP 1: Installing Docker ===')
run('apt-get update -qq')
run('apt-get install -y -qq ca-certificates curl')
run('install -m 0755 -d /etc/apt/keyrings')
run('curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc')
run('chmod a+r /etc/apt/keyrings/docker.asc')

codename, _ = run('. /etc/os-release && echo "$VERSION_CODENAME"')
print(f'Ubuntu codename: {codename}')

repo_cmd = f'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu {codename} stable" > /etc/apt/sources.list.d/docker.list'
run(repo_cmd)

run('apt-get update -qq')
out, err = run('apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin', timeout=120)
print(out[-300:] if len(out) > 300 else out)

v, _ = run('docker --version')
print(f'Docker: {v}')
vc, _ = run('docker compose version')
print(f'Compose: {vc}')

# Step 2: Clear old code and clone fresh
print('\n=== STEP 2: Setting up code ===')
run('rm -rf /root/leadforge')
run('cd /root && git clone https://github.com/pratikkshirsagar832-ctrl/Lead-forge-Ai-2.git leadforge')
out, _ = run('ls /root/leadforge/')
print(f'Files: {out}')

# Step 3: Create .env file with required secrets
print('\n=== STEP 3: Creating .env file ===')
env_content = """SUPABASE_URL=https://jrrslfopkfdldfjaznqd.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpycnNsZm9wa2ZkbGRmamF6bnFkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc3MDQ4NDUsImV4cCI6MjA2MzI4MDg0NX0.EkMH7fnmdjNfzHn1TY8H-DJsfyPNUwKvnK4yK5nOruI
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpycnNsZm9wa2ZkbGRmamF6bnFkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzcwNDg0NSwiZXhwIjoyMDYzMjgwODQ1fQ.e6vNsrf_Uu3qAKVk9F1uH0_QGRsBNje6cM8t0g-SjIE
GEMINI_API_KEY=AIzaSyASa_kOJil4PxyceNwnCaMEsJQIOd86TLc
FRONTEND_URL=https://hyperclients.ai
BACKEND_URL=http://localhost:8000
ENVIRONMENT=production
"""

# Write .env using heredoc via bash
run(f'cat > /root/leadforge/.env << ENVEOF\n{env_content}\nENVEOF')
out, _ = run('cat /root/leadforge/.env | head -5')
print(f'Env file: {out}')

# Step 4: Build and run with docker-compose
print('\n=== STEP 4: Building and starting containers ===')
out, err = run('cd /root/leadforge && docker compose build --no-cache 2>&1', timeout=600)
if err:
    print(f'Build ERR: {err[-500:]}')
print(f'Build: {out[-500:]}')

out, err = run('cd /root/leadforge && docker compose up -d 2>&1', timeout=60)
print(f'Up: {out}')
if err: print(f'Up ERR: {err}')

out, _ = run('docker ps')
print(f'Containers:\n{out}')

# Step 5: Set up nginx
print('\n=== STEP 5: Setting up nginx ===')
nginx_conf = """upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name hyperclients.ai www.hyperclients.ai 85.239.237.53;

    client_max_body_size 50M;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;
    gzip_min_length 1000;
    gzip_comp_level 6;

    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 90s;

        location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|webp|woff2?|ttf|eot)$ {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_cache_valid 200 7d;
            add_header Cache-Control "public, immutable";
            expires 7d;
        }
    }

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
"""

# Escape $ signs for shell
nginx_conf_escaped = nginx_conf.replace('$', '\\$')
run(f'cat > /etc/nginx/sites-available/hyperclients << NGINXEOF\n{nginx_conf_escaped}\nNGINXEOF')
run('ln -sf /etc/nginx/sites-available/hyperclients /etc/nginx/sites-enabled/')
run('rm -f /etc/nginx/sites-enabled/default')

# Test and restart nginx
out, err = run('nginx -t 2>&1')
print(f'Nginx test: {out}')

if 'test is successful' in out:
    run('systemctl restart nginx')
    print('Nginx restarted successfully')
else:
    print(f'Nginx config error: {err}')

# Step 6: Health check
print('\n=== STEP 6: Health check ===')
out, err = run('curl -s http://localhost:8000/api/health')
print(f'Backend health: {out}')
out, err = run('curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/')
print(f'Frontend status: {out}')
out, err = run('curl -s -o /dev/null -w "%{http_code}" http://85.239.237.53/')
print(f'Nginx status: {out}')

client.close()
print('\n=== DEPLOYMENT COMPLETE ===')
print('URL: http://85.239.237.53')
