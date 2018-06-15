import logging

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
_console_handler.setFormatter(_formatter)

log = logging.getLogger('electrum-merchant')
log.setLevel(logging.INFO)
log.addHandler(_console_handler)
