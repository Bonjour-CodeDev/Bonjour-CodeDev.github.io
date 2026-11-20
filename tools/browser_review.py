"""Render responsive previews with the runner's existing Chrome/ChromeDriver.

No third-party Python dependencies and no browser downloads are required.
"""
import argparse
import base64
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import traceback
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
report = {'commit': os.environ.get('GITHUB_SHA'), 'checks': [], 'screenshots': []}
driver = None
server = None
session = None

def request(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request('http://127.0.0.1:9515' + path, data=data, method=method,
                  headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=60) as response:
            return json.load(response).get('value')
    except HTTPError as error:
        raise RuntimeError(error.read().decode()) from error

def call(method, path, payload=None):
    return request(method, '/session/' + session + path, payload)

def script(source, *arguments):
    return call('POST', '/execute/sync', {'script': source, 'args': list(arguments)})

def cdp(command, parameters):
    return call('POST', '/goog/cdp/execute', {'cmd': command, 'params': parameters})

def wait_for(source, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if script(source):
            return
        time.sleep(.1)
    raise AssertionError('Timed out: ' + source)

def click(selector):
    script('document.querySelector(arguments[0]).scrollIntoView({block:"center",behavior:"instant"});', selector)
    element = call('POST', '/element', {'using': 'css selector', 'value': selector})
    element_id = element['element-6066-11e4-a52e-4f735466cecf']
    call('POST', '/element/' + element_id + '/click', {})

def screenshot(name):
    data = cdp('Page.captureScreenshot', {'format': 'jpeg', 'quality': 82, 'captureBeyondViewport': False})
    (args.output / (name + '.jpg')).write_bytes(base64.b64decode(data['data']))
    report['screenshots'].append(name + '.jpg')

def viewport(width, height):
    cdp('Emulation.setDeviceMetricsOverride', {
        'width': width, 'height': height, 'deviceScaleFactor': 1,
        'mobile': width < 600})
    time.sleep(.2)
    metrics = script('return {width: innerWidth, scroll: document.documentElement.scrollWidth};')
    assert metrics['width'] == width, metrics
    assert metrics['scroll'] <= width + 1, metrics
    report['checks'].append({'viewport': [width, height], 'horizontal_overflow': False})

def position(selector):
    script('document.querySelector(arguments[0]).scrollIntoView({block:"start",behavior:"instant"});', selector)
    time.sleep(.15)

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

try:
    executable = shutil.which('chromedriver')
    if not executable:
        candidate = Path(os.environ.get('CHROMEWEBDRIVER', '/usr/local/share/chromedriver-linux64')) / 'chromedriver'
        executable = str(candidate) if candidate.exists() else None
    assert executable, 'The runner must provide ChromeDriver; this script does not download it.'
    driver = subprocess.Popen([executable, '--port=9515', '--log-level=WARNING'], stdout=subprocess.DEVNULL)
    for _ in range(100):
        try:
            if request('GET', '/status')['ready']:
                break
        except OSError:
            time.sleep(.1)
    capabilities = {'browserName': 'chrome', 'goog:chromeOptions': {'args': [
        '--headless=new', '--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars',
        '--window-size=1440,1000', '--force-color-profile=srgb']},
        'goog:loggingPrefs': {'browser': 'ALL'}}
    result = request('POST', '/session', {'capabilities': {'alwaysMatch': capabilities}})
    session = result['sessionId']
    report['browser'] = result['capabilities']['browserVersion']
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    call('POST', '/url', {'url': 'http://127.0.0.1:' + str(server.server_port) + '/SCALER/'})
    script('document.documentElement.style.scrollBehavior="auto"; document.querySelectorAll(".paper-figure img").forEach(img=>img.loading="eager");')
    wait_for('return [...document.querySelectorAll(".paper-figure img")].every(img=>img.complete && img.naturalWidth>0);')
    assert script('return document.querySelectorAll(".paper-figure").length;') == 9
    report['checks'].append('All nine manuscript figures load')
    viewport(1024, 900)
    screenshot('laptop-hero')
    viewport(1440, 1000)
    screenshot('desktop-hero')
    position('#citation')
    screenshot('desktop-citation')
    position('#method')
    screenshot('desktop-method')
    position('#results')
    screenshot('desktop-results')
    position('#figure-case')
    screenshot('desktop-case')
    position('#figure-case-attn')
    screenshot('desktop-attention')
    click('#figure-case-attn [data-zoom]')
    wait_for('return document.querySelector("#figure-viewer").open && document.querySelector("#viewer-image").style.visibility==="visible";')
    screenshot('desktop-viewer')
    click('#zoom-actual')
    assert script('return document.querySelector("#zoom-level").textContent;') == '100%'
    assert script('return document.querySelector("#viewer-stage").scrollWidth > document.querySelector("#viewer-stage").clientWidth;')
    click('#zoom-in')
    assert script('return document.querySelector("#zoom-level").textContent;') == '140%'
    click('#zoom-out')
    assert script('return document.querySelector("#zoom-level").textContent;') == '100%'
    click('#zoom-fit')
    assert script('const e=document.querySelector("#viewer-stage"); return e.scrollWidth <= e.clientWidth+1 && e.scrollHeight <= e.clientHeight+1;')
    call('POST', '/actions', {'actions': [{'type': 'key', 'id': 'keyboard', 'actions': [
        {'type': 'keyDown', 'value': '\ue00c'}, {'type': 'keyUp', 'value': '\ue00c'}]}]})
    wait_for('return !document.querySelector("#figure-viewer").open && !document.body.classList.contains("viewer-open");')
    assert script('return document.activeElement.matches("#figure-case-attn [data-zoom]");'), script('return document.activeElement.outerHTML;')
    report['checks'].append('Figure viewer: fit, actual size, zoom, Escape, focus restoration, scroll restoration')
    click('.supplementary summary')
    assert script('return document.querySelector(".supplementary").open;')
    position('#figure-preliminary')
    screenshot('desktop-supplementary')
    click('.supplementary summary')
    for width in [768, 390, 320]:
        viewport(width, 900)
        script('window.scrollTo({top:0,behavior:"instant"});')
        wait_for('return document.querySelector(".nav-links [aria-current]") === null;')
        screenshot('mobile-hero' if width == 390 else 'viewport-' + str(width))
        if width == 390:
            position('#figure-case')
            screenshot('mobile-case')
            click('#figure-case [data-zoom]')
            wait_for('return document.querySelector("#figure-viewer").open && document.querySelector("#viewer-image").style.visibility==="visible";')
            screenshot('mobile-viewer')
            click('#zoom-actual')
            assert script('return document.querySelector("#zoom-level").textContent;') == '100%'
            click('#viewer-close')
            wait_for('return !document.querySelector("#figure-viewer").open;')
    errors = [entry for entry in call('POST', '/log', {'type': 'browser'}) if entry['level'] == 'SEVERE']
    assert not errors, errors
    report['checks'].append('No severe browser console errors')
    report['status'] = 'passed'
except Exception as error:
    report['status'] = 'failed'
    report['error'] = traceback.format_exc()
    if session:
        try:
            screenshot('failure')
        except Exception:
            pass
    raise
finally:
    (args.output/'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if session:
        request('DELETE', '/session/' + session)
    if driver:
        driver.terminate()
    if server:
        server.shutdown()
