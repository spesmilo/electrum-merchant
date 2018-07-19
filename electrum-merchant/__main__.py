import argparse
import errno
import io
import os
import requests
import shutil
import subprocess
import sys
import tarfile
import zipfile
from npmdownloader import NpmPackageDownloader
from .logger import log

_ROOT = os.path.abspath(os.path.dirname(__file__))

def get_data(path):
    return os.path.join(_ROOT, path)

def untar(fileName):
    log.info("Processing: %s into %s" % (fileName, os.path.dirname(fileName)))
    tar = tarfile.open(fileName)
    try:
        tar.extractall(path=os.path.dirname(fileName))
        log.info("Deleting %s" % fileName)
        os.unlink (fileName)
    except tar.TarError:
        log.error("Problems with extracting JavaScript library!")
    tar.close()

def walkFiles(dirName):
    dirs = os.walk(dirName)
    for (dirPath, dirNames, fileNames) in dirs:
        for dirName in dirNames:
            walkFiles(os.path.join(dirPath, dirName))
        for fileName in fileNames:
            if tarfile.is_tarfile(os.path.join(dirPath, fileName)):
                untar(os.path.join(dirPath, fileName))

def main():
    parser = argparse.ArgumentParser(description='Install merchant add on files\
                                     for Electrum wallet running in daemon mode.',
                                     prog = "python3 -m electrum-merchant",
                                     epilog = "Consult documentation on:\
                                     http://docs.electrum.org/en/latest/merchant.html",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-f', '--flavour', nargs='?', required=False, default="simple",
        help='Which merchant flavour should be installed [simple]'
    )
    parser.add_argument(
        '-n', '--network', nargs='?', required=False, default="mainnet",
        help='Coin network [mainnet, testnet]'
    )
    parser.add_argument(
        '-b', '--blockchain', nargs='?', required=False, default="BTC",
        help='Which blockchain we use [BTC, LTC, BCH, DASH]'
    )
    args = parser.parse_args()

    if args.blockchain == "BTC":
        from electrum import SimpleConfig
    elif args.blockchain == "LTC":
        from electrum_ltc import SimpleConfig
    elif args.blockchain == "BCH":
        from electroncash import SimpleConfig
    elif args.blockchain == "DASH":
        from electrum_dash import SimpleConfig
    else:
        log.error("Unknown blockchain, exiting...")
        exit(1)

    log.info('Downloading and installing files into request directory')
    if args.network == "mainnet":
        config = SimpleConfig()
    elif args.network == "testnet":
        config = SimpleConfig(options = {'testnet': True})
    else:
        log.error("Unknown network, exiting...")
        exit(1)

    rdir = config.get('requests_dir')
    if not rdir:
        log.error("requests_dir not found in Electrum configuration, exiting...")
        exit(1)
    sdir = os.path.join(rdir, 'static')
    if not os.path.exists(rdir):
        os.mkdir(rdir)
    if not os.path.exists(sdir):
        os.mkdir(sdir)

    # Copying the flavoured index.html
    log.info("copying index.html from flavour %s" % args.flavour)
    indexsrc = get_data(args.flavour + "/index.html")
    indexdst = os.path.join(rdir, 'index.html')
    shutil.copy(indexsrc, indexdst)

    # Downloading libraries from NPM registry and unpacking them
    downloader = NpmPackageDownloader(sdir)
    downloader.download('jquery')
    downloader.download('qrcodejs')
    walkFiles(sdir)

    # Downloading libraries from other sources and unpacking them
    # jquery-ui
    r = requests.get("https://code.jquery.com/ui/1.12.1/jquery-ui.min.js")
    if r.status_code == 200:
        with open(os.path.join(sdir, 'jquery-ui.min.js'), 'w') as f:
            f.write(r.text)
            log.info('Downloaded Jquery-UI.')
    else:
        log.error('Problems with downloading Jquery-UI.')
    # jquery-ui-fix-3
    r = requests.get("https://code.jquery.com/jquery-migrate-3.0.1.min.js")
    if r.status_code == 200:
        with open(os.path.join(sdir, 'jquery-migrate-3.0.1.js'), 'w') as f:
            f.write(r.text)
            log.info('Downloaded Jquery-UI 3.x fix.')
    else:
        log.error('Problems with downloading Jquery-UI.')
    # jquery-ui themes
    r = requests.get("https://jqueryui.com/resources/download/jquery-ui-themes-1.12.1.zip")
    if r.status_code == 200:
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(sdir)
        log.info('Downloaded Jquery-UI themes.')
    else:
        log.error('Problems with downloading Jquery-UI themes.')

    # Finally :-)
    log.info('Finished.')

if __name__ == '__main__':
    main()
