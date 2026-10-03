#!/usr/bin/env python3
"""Avialog local: Python 3.9+, SQLite, no third-party dependencies."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
import argparse, json, sqlite3, threading, webbrowser, datetime, math
ROOT=Path(__file__).resolve().parent
DB=ROOT/'dados'/'avialog.sqlite3'

def connect():
    conn=sqlite3.connect(DB,timeout=20)
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def invalid(message): raise ValueError(message)
def validate(w):
    if not isinstance(w,dict) or w.get('schema')!=1: invalid('Arquivo de trabalho incompatível.')
    for key,limit in [('routes',2000),('trucks',100),('records',10000),('scenarios',30)]:
        if not isinstance(w.get(key),list) or len(w[key])>limit: invalid('Limite ou formato inválido: '+key)
    c=w.get('config',{})
    limits={'days':(1,45),'fleet':(1,100),'unavailable':(0,100),'boxes':(1,1000),'density':(1,8),'loadMin':(1,600),'residenceMin':(1,600),'unloadMin':(1,300),'returnMin':(1,600),'delayMin':(0,360),'aveTarget':(0,500000),'realTarget':(0,500000),'aveOpen':(0,1439),'aveClose':(1,1440),'realOpen':(0,1439),'realClose':(1,1440),'saturdayTarget':(0,500000),'saturdayClose':(1,1440),'nightStart':(0,1439),'nightEnd':(0,1439),'creationLoss':(0,100)}
    for k,(low,high) in limits.items():
        v=c.get(k)
        if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or not low<=v<=high: invalid('Parâmetro inválido: '+k)
    datetime.date.fromisoformat(c['date'])
    if c['unloadMin']>c['residenceMin'] or c['aveOpen']>=c['aveClose'] or c['realOpen']>=c['realClose']: invalid('Tempos incompatíveis.')
    if c.get('stockMode') not in ['available','housed']: invalid('Base de aves inválida.')
    if c.get('nightOnly') and (c['nightEnd']-c['nightStart'])%1440<c['loadMin']: invalid('Janela noturna insuficiente.')
    ids=set()
    for r in w['routes']:
        if not all(isinstance(r.get(k),str) and r[k].strip() for k in ['id','farm','shed','city']): invalid('Granja, galpão e cidade são obrigatórios.')
        if r['id'] in ids: invalid('Identificador de rota repetido.')
        ids.add(r['id'])
        if not isinstance(r.get('birds'),int) or not 0<=r['birds']<=10000000: invalid('Quantidade de aves inválida.')
        for key in ['emptyMin','aveMin','realMin']:
            v=r.get(key)
            if v is None and key!='emptyMin': continue
            if not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1440: invalid('Tempo de rota inválido.')
        if r.get('destination') not in ['both','ave','real']: invalid('Destino inválido.')
        if r.get('blockedUntil'): datetime.date.fromisoformat(r['blockedUntil'])
    tids=set()
    for t in w['trucks']:
        if not isinstance(t.get('id'),str) or not t['id'] or t['id'] in tids or t.get('status') not in ['available','maintenance']: invalid('Frota inválida.')
        tids.add(t['id'])
    for r in w['records']:
        if not isinstance(r.get('loaded'),int) or r['loaded']<=0 or not isinstance(r.get('dead'),int) or not 0<=r['dead']<=r['loaded']: invalid('Registro de perdas inválido.')
        if not isinstance(r.get('minutes'),(int,float)) or r['minutes']<0 or r.get('plant') not in ['ave','real']: invalid('Registro de transporte inválido.')
        datetime.date.fromisoformat(r['date'])
    for s in w['scenarios']:
        validate({'schema':1,'config':s['config'],'routes':s['routes'],'trucks':s['trucks'],'records':[],'scenarios':[]})

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**k): super().__init__(*a,directory=str(ROOT/'web'),**k)
    def log_message(self,format,*args): pass
    def allowed_host(self):
        return self.headers.get('Host') in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
    def send_json(self,value,status=200):
        data=json.dumps(value,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if not self.allowed_host(): return self.send_json({'error':'Endereço não permitido.'},403)
        if urlsplit(self.path).path=='/api/workspace':
            try:
                with connect() as con: row=con.execute('SELECT data,revision FROM workspace WHERE id=1').fetchone()
                return self.send_json({'workspace':json.loads(row[0]),'revision':row[1]})
            except Exception: return self.send_json({'error':'Não foi possível carregar os dados.'},503)
        if self.path.startswith('/api/'): return self.send_json({'error':'Recurso não encontrado.'},404)
        return super().do_GET()
    def do_PUT(self):
        if not self.allowed_host(): return self.send_json({'error':'Endereço não permitido.'},403)
        if urlsplit(self.path).path!='/api/workspace': return self.send_json({'error':'Recurso não encontrado.'},404)
        origin=self.headers.get('Origin')
        if origin and origin not in [f'http://localhost:{self.server.server_port}',f'http://127.0.0.1:{self.server.server_port}']: return self.send_json({'error':'Origem não permitida.'},403)
        if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.send_json({'error':'Envie JSON.'},415)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>4000000: return self.send_json({'error':'Arquivo vazio ou maior que 4 MB.'},413)
            body=json.loads(self.rfile.read(size),parse_constant=lambda x:invalid('Número inválido.'))
            w=body['workspace'];rev=body['revision'];validate(w)
            if not isinstance(rev,int) or rev<0: invalid('Revisão inválida.')
            with connect() as con:
                updated=con.execute('UPDATE workspace SET data=?,revision=revision+1,updated_at=? WHERE id=1 AND revision=?',(json.dumps(w,ensure_ascii=False,allow_nan=False),datetime.datetime.now(datetime.timezone.utc).isoformat(),rev)).rowcount
                if not updated: return self.send_json({'error':'Os dados foram alterados em outra janela. Exporte sua cópia antes de recarregar.'},409)
            return self.send_json({'revision':rev+1})
        except (ValueError,TypeError,KeyError) as e: return self.send_json({'error':str(e)},400)
        except Exception: return self.send_json({'error':'Falha ao salvar. Seus dados anteriores foram preservados.'},503)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
    DB.parent.mkdir(exist_ok=True)
    with connect() as con:
        con.execute('CREATE TABLE IF NOT EXISTS workspace (id INTEGER PRIMARY KEY,data TEXT NOT NULL,revision INTEGER NOT NULL,updated_at TEXT NOT NULL)')
        con.execute('INSERT OR IGNORE INTO workspace VALUES (1,?,0,?)',((ROOT/'seed.json').read_text(encoding='utf-8'),datetime.datetime.now(datetime.timezone.utc).isoformat()))
    try: server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    except OSError as error:
        print('Não foi possível iniciar o servidor local: '+str(error));print('Se a porta estiver ocupada, use: python server.py --port 8766');return
    url=f'http://127.0.0.1:{server.server_port}'
    print('\nAVIALOG | Inteligência de Transporte\n'+url+'\n\nMantenha esta janela aberta. Ctrl+C encerra o sistema.\nDados salvos em: '+str(DB)+'\n',flush=True)
    if not args.no_browser: threading.Timer(.7,lambda:webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nSistema encerrado. Dados preservados.')
    finally: server.server_close()
if __name__=='__main__': main()
