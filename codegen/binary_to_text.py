import base64

__all__ = ('to_abc', 'from_abc')

_tab = bytes.maketrans(b'0123456789ABCDEF', b'GHIJKLMNOPABCDEF')
_rtab = bytes.maketrans(b'GHIJKLMNOPABCDEF', b'0123456789ABCDEF')

def to_abc(s):
    return base64.b16encode(s.encode()).translate(_tab).decode('ascii')

def from_abc(s):
    return base64.b16decode(s.encode().translate(_rtab)).decode('ascii')
