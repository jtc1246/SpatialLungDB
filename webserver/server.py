from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from _thread import start_new_thread
from time import sleep, time
import json
from myBasics import binToBase64
from mySecrets import hexToStr
import os
from queue import Queue
from R_http import fov_multi, gene_expression
from utils import convert_input, R_email_pipe, CELL_TYPES, GENES_FORMATTED_TO_ORIGIN, binary_to_str, pdf_to_png_bytes
from hashlib import sha256
from random import randint
from _thread import start_new_thread
from datetime import datetime, timezone
from ai import process_ai_chat


IS_SERVER = False
# IS_SERVER = True


NO_CACHE = 100000001
CACHE_ALL = 100000002

CACHE_MODE = NO_CACHE
if (IS_SERVER):
    CACHE_MODE = CACHE_ALL
BROWSER_CACHE = False
if (IS_SERVER):
    BROWSER_CACHE = True

USE_BUILT = False

registered = []

csses = os.listdir('./css')
jses = os.listdir('./js')
if USE_BUILT:
    jses = os.listdir('./js-build')
imgs = os.listdir('./imgs')


cached_files = {}


ROBOTS_TXT ='''
User-agent: *
Disallow: /*
Allow: /html/*
Allow: /index.html
Allow: /$
Allow: /sitemap.xml
Allow: /imgs/*
Allow: /data/*

Sitemap: http://128.84.8.183/sitemap.xml
'''


SITEMAP = '''
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>http://128.84.8.183/</loc>
    <lastmod>$lastmod-date$</lastmod>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>http://128.84.8.183/html/image.html</loc>
    <lastmod>$lastmod-date$</lastmod>
    <priority>0.4</priority>
  </url>
  <url>
    <loc>http://128.84.8.183/html/fov.html</loc>
    <lastmod>$lastmod-date$</lastmod>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>http://128.84.8.183/html/gene.html</loc>
    <lastmod>$lastmod-date$</lastmod>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>http://128.84.8.183/html/enrich.html</loc>
    <lastmod>$lastmod-date$</lastmod>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>http://128.84.8.183/html/dexp.html</loc>
    <lastmod>$lastmod-date$</lastmod>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>http://128.84.8.183/html/help.html</loc>
    <lastmod>$lastmod-date$</lastmod>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>http://128.84.8.183/html/about.html</loc>
    <lastmod>$lastmod-date$</lastmod>
    <priority>0.8</priority>
  </url>
</urlset>
'''

SITEMAP = SITEMAP.replace('$lastmod-date$', datetime.now(timezone.utc).strftime('%Y-%m-%d'))[1:]


def access_file(path: str, bin: bool):
    if (CACHE_MODE == CACHE_ALL and path in cached_files):
        data = cached_files[path]
    else:
        with open(path.replace('/js/', '/js-build/') if USE_BUILT else path, 'rb') as f:
            data = f.read()
        if (CACHE_MODE == CACHE_ALL):
            cached_files[path] = data
    if (bin):
        return data
    return data.decode('utf-8')

for css in csses:
    if (not css.endswith('.css')):
        continue
    registered.append(f'/css/{css}')

for js in jses:
    if (not js.endswith('.js')):
        continue
    registered.append(f'/js/{js}')

for img in imgs:
    tmp = img.lower()
    if (not tmp.endswith('.png') and not tmp.endswith('.jpg') and not tmp.endswith('.jpeg')  and not tmp.endswith('.gif')):
        continue
    registered.append(f'/imgs/{img}')


class Request(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path
        if (path == '/'):
            path = '/html/home.html'
        if (path == '/index.html'):
            path = '/html/home.html'
        if (path.startswith('/html/')):
            return self.process_html(path)
        if (path.startswith('/imgs/')):
            return self.process_img(path)
        if (path.startswith('/api/')):
            return self.process_get_api(path)
        if(path.startswith('/data/')):
            return self.process_server_data(path)
        if (path == '/robots.txt'):
            return self.process_robots_txt()
        if (path == '/sitemap.xml'):
            return self.process_sitemap_xml()
        return self.process_404(self)

    def do_POST(self) -> None:
        path = self.path
        if (path == '/chat'):
            return process_ai_chat(self, path)
        self.send_response(404)
        self.send_header('Connection', 'keep-alive')
        self.send_header('Content-Length', 13)
        self.end_headers()
        self.wfile.write(b'404 Not Found')
        self.wfile.flush()
        return

    def log_message(self, format, *args):
        pass
    
    def do_OPTIONS(self):
        print('http OPTIONS')
        self.send_response(200)
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Content-Length', 0)
        self.end_headers()
        self.wfile.write(b'')
        self.wfile.flush()
        return
    
    def process_robots_txt(self) -> None:
        self.send_response(200)
        self.send_header('Connection', 'keep-alive')
        self.send_header('Content-Length', len(ROBOTS_TXT.encode('utf-8')))
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Cache-Control', 'max-age=86400')
        self.end_headers()
        self.wfile.write(ROBOTS_TXT.encode('utf-8'))
        self.wfile.flush()
        return
    
    def process_sitemap_xml(self) -> None:
        self.send_response(200)
        self.send_header('Connection', 'keep-alive')
        self.send_header('Content-Length', len(SITEMAP.encode('utf-8')))
        self.send_header('Content-Type', 'application/xml')
        self.send_header('Cache-Control', 'max-age=86400')
        self.end_headers()
        self.wfile.write(SITEMAP.encode('utf-8'))
        self.wfile.flush()
        return
    
    def process_html(self, path: str) -> None:
        if (path.find('..') >= 0):
            return self.process_404(attack=True)
        # print(path)
        path = '.' + path
        try:
            html = access_file(path, False)
        except:
            return self.process_404()
        if (IS_SERVER):
            html = html.replace('<!--$jtc.unique.replacer$', '')
            html = html.replace('$jtc.unique.replacer$-->', '')
        for reg in registered:
            if (html.find(reg) == -1):
                continue
            file = access_file('.' + reg, True)
            file = binToBase64(file)
            if (reg.endswith('.css')):
                html = html.replace(reg, f'data:text/css;base64,{file}')
            if (reg.endswith('.js')):
                html = html.replace(reg, f'data:application/javascript;base64,{file}')
            if (reg.endswith('.png')):
                html = html.replace(reg, f'data:image/png;base64,{file}')
            if (reg.endswith('.jpg') or reg.endswith('.jpeg')):
                html = html.replace(reg, f'data:image/jpeg;base64,{file}')
            if (reg.endswith('.gif')):
                html = html.replace(reg, f'data:image/gif;base64,{file}')
        html = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Connection', 'keep-alive')
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(html))
        if (BROWSER_CACHE):
            self.send_header('Cache-Control', 'max-age=300')
        self.end_headers()
        self.wfile.write(html)
        self.wfile.flush()
        return
    
    def process_server_data(self, path: str) -> None:
        if(IS_SERVER == False):
            return self.process_404()
        if (path.find('..') >= 0):
            return self.process_404(attack=True)
        if('webserver' in path):
            return self.process_404()
        if(path.endswith('.xlsx')):
            return self.process_404()
        if(path.endswith('.R')):
            return self.process_404()
        path = path[6:]
        path = path.replace('@', ' ')
        path = '../' + path
        try:
            data = access_file(path, True)
        except:
            return self.process_404()
        self.send_response(200)
        self.send_header('Connection', 'keep-alive')
        self.send_header('Content-Type', 'image/png')
        self.send_header('Content-Length', len(data))
        if ('slide' in path):
            self.send_header('Cache-Control', f'max-age={3600*24*90}')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)
        self.wfile.flush()
        return
        
    
    def process_img(self, path: str) -> None:
        return self.process_404(attack=True)
    
    
    def process_404(self, attack=False) -> None:
        self.send_response(404)
        self.send_header('Connection', 'keep-alive')
        self.send_header('Content-Length', 13)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'404 Not Found')
        self.wfile.flush()
        return
    
    def process_get_api(self, path: str) -> None:
        path = path[4:]
        if (path.startswith('/email_multi/')):
            # print(path)
            success, msg, result = convert_input(path[13:])
            if (success == False):
                msg = "ERROR: \n" + msg
                print(msg)
                msg = msg.encode('utf-8')
                self.send_response(400)
                self.send_header('Connection', 'keep-alive')
                self.send_header('Content-Length', len(msg))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(msg)
                self.wfile.flush()
                return
            print(result)
            host = self.headers['Host']
            task_id = sha256((f'{result[0]}_{result[1]}_{result[2]}_{result[3]}').encode('utf-8')).hexdigest()
            ran = randint(0, 100000000000)
            file_name = sha256((f'{task_id}_{ran}_{time()}').encode('utf-8')).hexdigest()
            file_name += '.pdf'
            start_new_thread(R_email_pipe, (task_id, file_name, result[0], result[1], result[2], result[3], result[4], host))
            self.send_response(202)
            self.send_header('Connection', 'keep-alive')
            self.send_header('Content-Length', 0)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'')
            self.wfile.flush()
            return
        if (path.startswith('/generated/')):
            path = path[11:]
            if ('..' in path):
                return self.process_404(attack=True)
            path = '../tmp/' + path
            try:
                with open(path, 'rb') as f:
                    png = f.read()
            except:
                return self.process_404()
            self.send_response(200)
            self.send_header('Connection', 'keep-alive')
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', len(png))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(png)
            self.wfile.flush()
            return
        if (path.startswith('/gene_exp/')):
            path = path[10:]
            data = hexToStr(path)
            data = json.loads(data)
            genes = data['genes']
            cell_types = data['cell_types']
            cell_type_names = ''
            cnt_tmp = 0
            for selected in cell_types:
                cnt_tmp += 1
                if (selected):
                    cell_type_names += CELL_TYPES[cnt_tmp - 1] + ','
            assert (cell_type_names != '')
            cell_type_names = cell_type_names[:-1]
            assert (len(genes) > 0)
            my_genes = []
            for g in genes:
                assert (g in GENES_FORMATTED_TO_ORIGIN)
                my_genes.append(GENES_FORMATTED_TO_ORIGIN[g])
            if (len(set(my_genes)) != len(my_genes)):
                self.send_response(500)
                self.send_header('Connection', 'keep-alive')
                self.send_header('Access-Control-Allow-Origin', '*')
                msg = json.dumps({'msg': "Genes cannot be duplicated!"}, ensure_ascii=False).encode('utf-8')
                self.send_header('Content-Length', len(msg))
                self.end_headers()
                self.wfile.write(msg)
                self.wfile.flush()
                return
            my_genes.sort()
            genes = ','.join(my_genes)
            t = str(time())
            task_id = sha256((f'{genes}_{cell_type_names}_{t}').encode('utf-8')).hexdigest()
            resp = gene_expression(genes, cell_type_names, f'./tmp/{task_id}.pdf')
            if (resp[0] == False):
                self.send_response(500)
                self.send_header('Connection', 'keep-alive')
                self.send_header('Access-Control-Allow-Origin', '*')
                msg = binary_to_str(resp[1])
                msg = json.dumps({'msg': msg}, ensure_ascii=False).encode('utf-8')
                self.send_header('Content-Length', len(msg))
                self.end_headers()
                self.wfile.write(msg)
                self.wfile.flush()
                return
            file_path = f'../docker/resources/04.exp_functions/tmp/{task_id}.pdf'
            png_bytes = pdf_to_png_bytes(file_path)
            png_base64 = binToBase64(png_bytes)
            data = json.dumps({'img': png_base64}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Connection', 'keep-alive')
            self.send_header('Content-Length', len(data))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
            self.wfile.flush()
            return
        return self.process_404()


pp = 9035
if(IS_SERVER):
    pp = 80
server = ThreadingHTTPServer(('0.0.0.0', pp), Request)
start_new_thread(server.serve_forever, ())
while True:
    sleep(10)