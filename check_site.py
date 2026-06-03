import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('81.68.209.235', username='root', password='m848599878M')

# Test with correct Host header from outside
cmds = [
    'curl -s -o /dev/null -w "%{http_code}" -H "Host: 81.68.209.235" http://127.0.0.1/',
    'curl -s -H "Host: 81.68.209.235" http://127.0.0.1/ | head -3',
]

for cmd in cmds:
    print(f'>>> {cmd}')
    stdin, stdout, stderr = c.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out.strip(): print(out.strip())
    if err.strip(): print('ERR:', err.strip())

c.close()
