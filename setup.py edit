
import urllib, shutil, os
from electrum import SimpleConfig


if __name__ == "__main__":

    config= SimpleConfig()
    rdir = config.get('requests_dir')
    if not rdir:
        print("requests_dir not found in Electrum configuration")
        exit(1)
    if not os.path.exists(rdir):
        os.mkdir(rdir)
    index = os.path.join(rdir, 'index.html')
    print("copying index.html")
    src = os.path.join(os.path.dirname(__file__), 'www', 'index.html')
    shutil.copy(src, index)
    files = [
        "https://code.jquery.com/jquery-1.9.1.min.js",
        "https://raw.githubusercontent.com/davidshimjs/qrcodejs/master/qrcode.js",
        "https://code.jquery.com/ui/1.10.3/jquery-ui.js",
        "https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css"
    ]
    for URL in files:
        path = urllib.parse.urlsplit(URL).path
        filename = os.path.basename(path)
        path = os.path.join(rdir, filename)
        if not os.path.exists(path):
            print("downloading ", URL)
            urllib.request.urlretrieve(URL, path)
