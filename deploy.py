"""
Deploy K歌 Cookie Updater to server
"""
import paramiko

HOST = '81.68.209.235'
USER = 'root'
PASS = 'm848599878M'

def run(c, cmd, timeout=None):
    print(f'>>> {cmd[:100]}...')
    stdin, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out.strip():
        for line in out.strip().split('\n')[-8:]:
            print('   ', line)
    if err.strip():
        print('ERR:', err.strip()[-300:])
    return out, err

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS)

    # Step 1: Recompile Python with OpenSSL 1.1.1
    print("\n=== Step 1: Recompile Python with OpenSSL 1.1.1 ===")
    run(c, 'cd /tmp/Python-3.11.9 && make clean 2>&1 | tail -1')
    run(c, 'cd /tmp/Python-3.11.9 && ./configure --prefix=/usr/local/python311 --with-openssl=/usr/local/openssl111 --with-openssl-rpath=auto 2>&1 | tail -3')
    print("Building Python... (takes a few minutes)")
    run(c, 'cd /tmp/Python-3.11.9 && make -j$(nproc) 2>&1 | tail -3', timeout=300)
    run(c, 'cd /tmp/Python-3.11.9 && make install 2>&1 | tail -3', timeout=120)

    # Verify SSL
    out, err = run(c, '/usr/local/python311/bin/python3.11 -c "import ssl; print(\'SSL OK:\', ssl.OPENSSL_VERSION)"')
    if 'SSL OK' not in out:
        print("FATAL: SSL still not working")
        c.close()
        return

    # Step 2: Install project dependencies
    print("\n=== Step 2: Install dependencies ===")
    run(c, '/usr/local/python311/bin/pip3.11 install flask pymysql requests pyqrcode gunicorn 2>&1 | tail -5')

    # Step 3: Set up project directory
    print("\n=== Step 3: Set up project ===")
    run(c, 'cd /opt/kg-cookie-updater && /usr/local/python311/bin/pip3.11 install -r requirements.txt 2>&1 | tail -5')
    run(c, 'cd /opt/kg-cookie-updater && /usr/local/python311/bin/python3.11 -c "from flask import Flask; print(\'Flask OK\'); from kg_login import Login; print(\'kg_login OK\')"')

    # Step 4: Stop old service if exists
    print("\n=== Step 4: Configure systemd ===")
    run(c, 'systemctl stop kg-cookie 2>/dev/null; echo "stopped"')

    service_unit = """[Unit]
Description=KG Cookie Updater
After=network.target

[Service]
User=root
WorkingDirectory=/opt/kg-cookie-updater
ExecStart=/usr/local/python311/bin/gunicorn app:app --bind 127.0.0.1:9000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    # Write service file line by line
    lines = service_unit.strip().split('\n')
    run(c, '> /etc/systemd/system/kg-cookie.service')
    for line in lines:
        run(c, f"echo '{line}' >> /etc/systemd/system/kg-cookie.service")
    run(c, 'cat /etc/systemd/system/kg-cookie.service')
    run(c, 'systemctl daemon-reload && systemctl enable kg-cookie && systemctl start kg-cookie')
    out, _ = run(c, 'systemctl status kg-cookie --no-pager 2>&1 | head -15')

    # Step 5: Configure Nginx (Baota panel path)
    print("\n=== Step 5: Configure Nginx ===")
    nginx_lines = [
        'server {',
        '    listen 80;',
        '    server_name _;',
        '',
        '    location / {',
        '        proxy_pass http://127.0.0.1:9000;',
        "        proxy_set_header Host $host;",
        "        proxy_set_header X-Real-IP $remote_addr;",
        "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
        "        proxy_set_header X-Forwarded-Proto $scheme;",
        '    }',
        '',
        '    location /static {',
        '        alias /opt/kg-cookie-updater/static;',
        '    }',
        '}',
    ]
    run(c, '> /www/server/nginx/conf/vhost/kg-cookie.conf')
    for line in nginx_lines:
        escaped = line.replace("'", "'\"'\"'")
        run(c, f"echo '{line}' >> /www/server/nginx/conf/vhost/kg-cookie.conf")
    run(c, 'cat /www/server/nginx/conf/vhost/kg-cookie.conf')
    run(c, 'nginx -t 2>&1')
    run(c, 'systemctl reload nginx 2>&1')

    # Step 6: Verify
    print("\n=== Step 6: Verify ===")
    run(c, 'sleep 2 && curl -s http://127.0.0.1/ | head -10')

    print("\n=== DEPLOYMENT COMPLETE ===")
    print("Access at: http://81.68.209.235/")

    c.close()

if __name__ == '__main__':
    main()
