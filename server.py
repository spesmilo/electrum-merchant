import asyncio
from collections import defaultdict
import datetime
import json
import os
import sys
import time

import aiohttp

from electrum import constants
from electrum.daemon import Daemon
from electrum.wallet import Wallet
from electrum.storage import WalletStorage
from electrum.simple_config import SimpleConfig
from electrum.util import set_verbosity
from electrum.lnaddr import lndecode

from aiohttp import web, helpers
from aiohttp.web_runner import TCPSite, AppRunner
from aiohttp.log import access_logger

set_verbosity(True)

user_dir = sys.argv[1]

assert os.path.exists(user_dir)

constants.set_regtest()
config = SimpleConfig({
    #"dynamic_fees": False,
    "auto_connect": False,
    "oneserver": True,
    "server": "localhost:51001:t",
    "regtest": True,
    }, read_user_dir_function=lambda: user_dir)
actual = Daemon(config)
assert actual.network.asyncio_loop.is_running()
storage = WalletStorage(config.get_wallet_path())
assert not storage.is_encrypted()
wallet = Wallet(storage)
wallet.start_network(actual.network)
actual.add_wallet(wallet)

async def create_invoice(request):
    params = await request.post()
    if 'amt_msat' not in params or not params['amt_msat'].isdigit():
        raise web.HTTPUnsupportedMediaType()
    amt_msat = int(params['amt_msat'])
    if amt_msat == 0:
        raise web.HTTPUnsupportedMediaType()
    inv = wallet.lnworker.add_invoice(amt_msat, "donation")
    print("invoice created", inv)
    assert inv_to_payment_hash(inv) in wallet.lnworker.invoices
    raise web.HTTPFound('/static/invoice_status.html?' + inv)

q = defaultdict(asyncio.Event)

async def put_on_queue(evt, time, direction, htlc, preimage, chan_id):
    for this_preimage, invoice, direction, time in wallet.lnworker.invoices.values():
        if preimage == this_preimage:
            await q[invoice].set()
            break
    else:
        raise Exception(f"could not find invoice with preimage {preimage}")

wallet.network.register_callback(put_on_queue, ['ln_payment_completed'])

def inv_to_payment_hash(inv):
    return lndecode(inv, expected_hrp=constants.net.SEGWIT_HRP).paymenthash.hex()

async def ln_websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    invoice = request.query_string
    try:
        _, _, _, date = wallet.lnworker.invoices[inv_to_payment_hash(invoice)]
    except KeyError:
        await ws.send_str('unknown invoice, try creating a new invoice for donating')
        await ws.close()
        return ws

    if date is not None:
        await ws.send_str(f'already paid at {date}')
        await ws.close()
        return ws

    while True:
        try:
            await asyncio.wait_for(q[invoice].wait(), 1)
        except asyncio.TimeoutError:
            await ws.send_str(f'still not paid at {datetime.datetime.now()}')
        else:
            await ws.send_str(f'payment received at {datetime.datetime.now()}')
            break

    await ws.close()

    return ws

def read_request(request_id):
    global rdir
    # read json file
    n = os.path.join(rdir, 'req', request_id[0], request_id[1], request_id, request_id + '.json')
    with open(n, encoding='utf-8') as f:
        s = f.read()
    d = json.loads(s)
    addr = d.get('address')
    amount = d.get('amount')
    return addr, amount

async def bip70_websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if not msg.data.startswith('id:'):
                ws.close()
                break
            req_id = msg.data[3:]
            addr, amount = read_request(req_id)
            while sum(wallet.get_addr_balance(addr)) < amount:
                await wallet.wait_for_address_history_to_change(addr)
            await ws.send_str('paid')
            await ws.close()
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())
            break

rdir = config.get('requests_dir')
assert rdir

async def on_response_prepare(request, response):
    if request.path.startswith('/req') and not request.path.endswith('.json'):
        response.headers['Content-type'] = 'application/bitcoin-paymentrequest'

app = web.Application(loop=actual.network.asyncio_loop)

app.on_response_prepare.append(on_response_prepare)

app.add_routes([web.post('/api/ln/create_invoice', create_invoice)])
app.add_routes([web.get('/api/ln/invoice_status', ln_websocket_handler)])
app.add_routes([web.get('/api/bip70_invoice_status', bip70_websocket_handler)])
app.add_routes([web.static('/static', 'static')])
app.add_routes([web.static('/req', rdir + '/req')])

runner = AppRunner(app, handle_signals=False,
                   access_log_class=helpers.AccessLogger,
                   access_log_format=helpers.AccessLogger.LOG_FORMAT,
                   access_log=access_logger)

asyncio.run_coroutine_threadsafe(runner.setup(), actual.network.asyncio_loop).result()

host, port = "127.0.0.1", 8000
site = TCPSite(runner, port=port, host=host)
asyncio.run_coroutine_threadsafe(site.start(), actual.network.asyncio_loop).result()
while True:
    print(f"Still serving on http://{host}:{port}")
    time.sleep(5)
