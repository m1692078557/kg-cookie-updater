import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('81.68.209.235', username='root', password='m848599878M')

config = r"""server {
    listen 80;
    server_name _;

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
}"""

cmd = "cat > /www/server/panel/vhost/nginx/kg-cookie.conf << 'NGINXEOF'\n" + config + "\nNGINXEOF"
stdin, stdout, stderr = c.exec_command(cmd)
out = stdout.read().decode()
err = stderr.read().decode()
print('Write:', out, err)

for cmd in [
    'cat /www/server/panel/vhost/nginx/kg-cookie.conf',
    'nginx -t 2>&1',
    'systemctl reload nginx 2>&1',
]:
    print(f'\n>>> {cmd}')
    stdin, stdout, stderr = c.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out.strip(): print(out.strip())
    if err.strip(): print('ERR:', err.strip())

# Final test
stdin, stdout, stderr = c.exec_command('curl -s http://127.0.0.1/ | head -3')
print('\n>>> curl test:')
print(stdout.read().decode())

c.close()
