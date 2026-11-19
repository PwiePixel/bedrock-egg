#!/usr/bin/env python3
"""Aktiviert das Experiment "Beta APIs" (gametest) in einer Bedrock level.dat.
Benutzung: enable_beta_api.py <pfad/zur/level.dat>
Exit-Code 0 = gesetzt bzw. schon aktiv, 1 = Fehler."""
import shutil
import struct
import sys

END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BARR, STR, LIST, COMP, IARR, LARR = range(13)


class R:
    def __init__(self, b):
        self.b, self.i = b, 0

    def take(self, n):
        v = self.b[self.i:self.i + n]
        self.i += n
        return v

    def u(self, fmt):
        n = struct.calcsize(fmt)
        return struct.unpack("<" + fmt, self.take(n))[0]

    def s(self):
        return self.take(self.u("H")).decode("utf-8", "surrogateescape")


def read_payload(r, t):
    if t == BYTE: return r.u("b")
    if t == SHORT: return r.u("h")
    if t == INT: return r.u("i")
    if t == LONG: return r.u("q")
    if t == FLOAT: return r.u("f")
    if t == DOUBLE: return r.u("d")
    if t == BARR: return r.take(r.u("i"))
    if t == STR: return r.s()
    if t == LIST:
        et, n = r.u("b"), r.u("i")
        return (et, [read_payload(r, et) for _ in range(n)])
    if t == COMP:
        d = []
        while True:
            ct = r.u("b")
            if ct == END:
                return d
            name = r.s()
            d.append([ct, name, read_payload(r, ct)])
    if t == IARR: n = r.u("i"); return list(struct.unpack("<%di" % n, r.take(4 * n)))
    if t == LARR: n = r.u("i"); return list(struct.unpack("<%dq" % n, r.take(8 * n)))
    raise ValueError("unbekannter Tag %d" % t)


def ws(s):
    b = s.encode("utf-8", "surrogateescape")
    return struct.pack("<H", len(b)) + b


def write_payload(t, v):
    if t == BYTE: return struct.pack("<b", v)
    if t == SHORT: return struct.pack("<h", v)
    if t == INT: return struct.pack("<i", v)
    if t == LONG: return struct.pack("<q", v)
    if t == FLOAT: return struct.pack("<f", v)
    if t == DOUBLE: return struct.pack("<d", v)
    if t == BARR: return struct.pack("<i", len(v)) + v
    if t == STR: return ws(v)
    if t == LIST:
        et, items = v
        return struct.pack("<bi", et, len(items)) + b"".join(write_payload(et, x) for x in items)
    if t == COMP:
        return b"".join(struct.pack("<b", ct) + ws(n) + write_payload(ct, p) for ct, n, p in v) + b"\x00"
    if t == IARR: return struct.pack("<i", len(v)) + struct.pack("<%di" % len(v), *v)
    if t == LARR: return struct.pack("<i", len(v)) + struct.pack("<%dq" % len(v), *v)
    raise ValueError(t)


def set_byte(comp, name, val):
    for e in comp:
        if e[1] == name:
            e[0], e[2] = BYTE, val
            return
    comp.append([BYTE, name, val])


def main(path):
    data = open(path, "rb").read()
    version = struct.unpack("<i", data[0:4])[0]
    r = R(data[8:])
    rt = r.u("b")
    rname = r.s()
    root = read_payload(r, rt)
    exp = next((e for e in root if e[1] == "experiments" and e[0] == COMP), None)
    if exp is None:
        exp = [COMP, "experiments", []]
        root.append(exp)
    if any(e[1] == "gametest" and e[2] == 1 for e in exp[2]):
        print("Beta APIs bereits aktiv")
        return 0
    set_byte(exp[2], "gametest", 1)
    set_byte(exp[2], "experiments_ever_used", 1)
    set_byte(exp[2], "saved_with_toggled_experiments", 1)
    body = struct.pack("<b", rt) + ws(rname) + write_payload(rt, root)
    shutil.copy2(path, path + ".bak")
    open(path, "wb").write(struct.pack("<ii", version, len(body)) + body)
    print("Beta APIs aktiviert")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1]))
    except Exception as ex:  # noqa
        print("Fehler beim Bearbeiten der level.dat:", ex)
        sys.exit(1)
