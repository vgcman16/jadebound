#!/usr/bin/env python3
import subprocess, pathlib, time, os, sys
root=pathlib.Path(__file__).resolve().parents[1]
logs=root/'builds'; logs.mkdir(exist_ok=True)
env=os.environ.copy()
for key,sub in [('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config')]:
    env[key]=str(root/'local'/sub)
children=[]
handles=[]
try:
    for role,args in [('server',['--server','--stop-after=10']),('client1',['--network-probe','--connect=127.0.0.1','--stop-after=6']),('client2',['--network-probe','--connect=127.0.0.1','--stop-after=6'])]:
        handle=(logs/f'network-{role}.log').open('w'); handles.append(handle)
        proc=subprocess.Popen(['godot','--headless','--path',str(root/'game'),'--',*args],stdout=handle,stderr=subprocess.STDOUT,env=env)
        children.append((role,proc))
        time.sleep(.8 if role=='server' else .15)
    for role,proc in children:
        rc=proc.wait(timeout=15)
        print(role,'exit',rc)
        if rc:raise RuntimeError(f'{role} failed')
    for role in ['client1','client2']:
        text=(logs/f'network-{role}.log').read_text()
        print(text.strip())
        if 'own_player=true' not in text:raise RuntimeError(f'{role} did not receive authoritative own state')
    print('JADE_NETWORK_TEST_PASSED server + two clients')
finally:
    for role,proc in children:
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=2)
            except subprocess.TimeoutExpired:proc.kill(); proc.wait()
    for handle in handles:handle.close()
