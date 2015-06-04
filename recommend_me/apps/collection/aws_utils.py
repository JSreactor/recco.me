import hmac as _hmac
import base64
import urllib
from hashlib import sha1 as sha
from hashlib import sha256 as sha256


def get_utf8_value(value):
    if not isinstance(value, str) and not isinstance(value, unicode):
        value = str(value)
    if isinstance(value, unicode):
        return value.encode('utf-8')
    else:
        return value


def calc_signature_0(params, secret_key):
    hmac = _hmac.new(get_utf8_value(secret_key), digestmod=sha)
    s = params['Action'] + params['Timestamp']
    hmac.update(s)
    keys = params.keys()
    keys.sort(cmp=lambda x, y: cmp(x.lower(), y.lower()))
    pairs = []
    for key in keys:
        val = get_utf8_value(params[key])
        pairs.append(key + '=' + urllib.quote(val))
    qs = '&'.join(pairs)
    return (qs, base64.b64encode(hmac.digest()))


def calc_signature_1(params, secret_key):
    hmac = _hmac.new(get_utf8_value(secret_key), digestmod=sha)
    keys = params.keys()
    keys.sort(cmp=lambda x, y: cmp(x.lower(), y.lower()))
    pairs = []
    for key in keys:
        hmac.update(key)
        val = get_utf8_value(params[key])
        hmac.update(val)
        pairs.append(key + '=' + urllib.quote(val))
    qs = '&'.join(pairs)
    return (qs, base64.b64encode(hmac.digest()))


def calc_signature_2(params, verb, path, secret_key, server_name='hstreaming.com', hmac_256=False):
    string_to_sign = '%s\n%s\n%s\n' % (verb, server_name, path)
    if hmac_256:
        hmac = _hmac.new(get_utf8_value(secret_key), digestmod=sha256)
        params['SignatureMethod'] = 'HmacSHA256'
    else:
        hmac = _hmac.new(get_utf8_value(secret_key), digestmod=sha)
        params['SignatureMethod'] = 'HmacSHA1'
    keys = params.keys()
    keys.sort()
    pairs = []
    for key in keys:
        val = get_utf8_value(params[key])
        pairs.append(urllib.quote(key, safe='') + '=' + urllib.quote(val, safe='-_~'))
    qs = '&'.join(pairs)
    string_to_sign += qs
    hmac.update(string_to_sign)
    b64 = base64.b64encode(hmac.digest())
    return (qs, b64)


def get_signature(params, verb, path, secret_key, SignatureVersion='2', server_name='webservices.amazon.com', hmac_256=False):
    if SignatureVersion == '0':
        t = calc_signature_0(params, secret_key)
    elif SignatureVersion == '1':
        t = calc_signature_1(params, secret_key)
    elif SignatureVersion == '2':
        t = calc_signature_2(params, verb, path, secret_key, server_name, hmac_256)
    else:
        raise Exception('Unknown Signature Version: %s' % SignatureVersion)
    return t
