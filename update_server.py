import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('81.68.209.235', username='root', password='m848599878M')

for cmd in [
    'cd /opt/kg-cookie-updater && git pull 2>&1',
    'systemctl restart kg-cookie && systemctl status kg-cookie --no-pager 2>&1 | head -8',
    'curl -s -H "Host: 81.68.209.235" http://127.0.0.1/ | head -3',
]:
    print(f'>>> {cmd}')
    stdin, stdout, stderr = c.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out.strip(): print(out.strip())
    if err.strip(): print(err.strip())
    print()

c.close()
print('Updated!')
