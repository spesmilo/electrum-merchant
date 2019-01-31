Electrum-merchant
-----------------
This is an add-on to Electrum wallet, which allows Electrum to function as a payment service.

It supports BIP-70 invoices and Lightning.

For BIP-70, you need to create a directory for invoices and configure Electrum with ``requests_dir`` set and ``url_rewrite`` set::

    # in electrum-merchant root directory
    # make directory for BIP-70 invoices, which the webserver will serve
    mkdir -p requests/req
    run_electrum --testnet setconfig requests_dir $PWD/requests
    # the second argument should be the publicly accessible root URL of the webserver served by server.py
    run_electrum --testnet setconfig url_rewrite "[ 'file://$PWD/requests', 'http://127.0.0.1:8080/' ]"

To install static resources into the ``static`` directory (which will be served by the webserver in ``server.py``)::

    python3 -m electrum-merchant

Currently, only testnet is supported. To run, the server (maybe run this in ``screen`` to be able to background it)::

    python3 server.py ~/.electrum # argument is your user_dir. 'testnet' will be appended to this!

BIP-70
------

You can generate an invoice using::

    run_electrum --testnet addrequest 3.14 -m "this is a test"

Click the ``index_url`` link in the JSON outputted, and you'll see a page that presents the invoice. When the invoice is paid, the webpage will say so.

Lightning
---------

Generate an invoice using::

    run_electrum --testnet addinvoice 3.14 "this is a test"

Or using http://127.0.0.1:8080/static/create_invoice.html

If you use the second method, the user will be redirected to the invoice status page.

If you use the first method, take the BOLT-11 invoice (``lntb1...``) and append it to ``http://127.0.0.1:8080/static/invoice_status.html?``. The invoice is the whole query string.
