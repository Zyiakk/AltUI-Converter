"""--selftest: detect and convert one synthetic body, weapon and idle mod without a window.
Run after every build, so a module PyInstaller left out shows up before a user meets it."""
import os, sys, tempfile
from altui_tool import detect, fixtures, jobs


def aes_check():
    """The game pak is AES encrypted; weaponpak reads it for a weapon that brings its own shot sound. One FIPS-197 block on
    the path pak11_extract takes in the build (no cryptography there), and the key search: the key is never shipped, it
    is put together from the moves of the game exe's key function (here a synthetic one)."""
    try:
        import pak11_extract as p
        key = bytes(range(32))
        ok = p.aes(bytes.fromhex("8ea2b7ca516745bfeafc49904b496089"), key) == bytes.fromhex("00112233445566778899aabbccddeeff")
        code = b"".join(b"\xC7\x45" + bytes([0xE0 + 4 * i]) + key[4 * i:4 * i + 4] + (b"\x0F\x10\x45\xE0" if i == 3 else b"")
                        for i in range(8))
        ok = ok and key in p.key_candidates(b"\xCC" * 64 + code + b"\xC3")
        return ok, "%s aes: game pak decryption, key from the game exe" % ("OK" if ok else "FAIL")
    except Exception as e:
        return False, "FAIL aes: %s: %s" % (type(e).__name__, e)


def run(report=None):
    lines, ok = [], True
    with tempfile.TemporaryDirectory(prefix="altui-selftest-") as d:
        altui = fixtures.altui_pak(os.path.join(d, "AltUI.pak"))
        cases = [("body", fixtures.body_pak(os.path.join(d, "Body_P.pak")), {}),
                 ("weapon", fixtures.weapon_skin_pak(os.path.join(d, "ump45.pak")), {}),
                 ("idle", fixtures.idle_pak(os.path.join(d, "Idle_P.pak")), {"altui_pak": altui})]
        for kind, src, extra in cases:
            found = detect.detect(src).kind
            res = jobs.execute(jobs.Job(kind, src, "SelfTest", "Self test", os.path.join(d, "out"), **extra))
            good = found == kind and res.ok and os.path.isfile(res.pak or "")
            ok = ok and good
            lines.append("%s %s: detected %s; %s" % ("OK" if good else "FAIL", kind, found, res.summary))
            if not good:
                lines += ["  " + x for x in res.details]
    good, line = aes_check()
    ok = ok and good
    lines.append(line)
    text = "\n".join(lines + ["selftest " + ("passed" if ok else "FAILED")]) + "\n"
    if report:
        with open(report, "w", encoding="utf-8") as f:
            f.write(text)
    if sys.stdout:
        sys.stdout.write(text)
    return 0 if ok else 1
