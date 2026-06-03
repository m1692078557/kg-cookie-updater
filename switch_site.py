import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('81.68.209.235', username='root', password='m848599878M')

# Replace the existing site config to proxy to Flask
config = r"""server
{
    listen 80;
    server_name 81.68.209.235 tscat.asia www.tscat.asia;
    index index.html;

    # Flask proxy
    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/kg-cookie-updater/static;
    }

    access_log  /www/wwwlogs/81.68.209.235.log;
    error_log  /www/wwwlogs/81.68.209.235.error.log;
}"""

cmd = "cat > /www/server/panel/vhost/nginx/81.68.209.235.conf << 'NGXEOF'\n" + config + "\nNGXEOF"
stdin, stdout, stderr = c.exec_command(cmd)
print('Write:', stdout.read().decode(), stderr.read().decode())

# Test and reload
for cmd in [
    'cat /www/server/panel/vhost/nginx/81.68.209.235.conf',
    'nginx -t 2>&1',
    'systemctl reload nginx 2>&1',
    'systemctl status kg-cookie --no-pager 2>&1 | head -10',
]:
    print(f'\n--- {cmd}')
    stdin, stdout, stderr = c.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out.strip(): print(out.strip())
    if err.strip(): print(err.strip())

# Test access
stdin, stdout, stderr = c.exec_command('curl -s http://127.0.0.1/ | head -15')
print('\n--- curl test:')
print(stdout.read().decode())

c.close()
print('\nDone! Access: http://81.68.209.235/')
