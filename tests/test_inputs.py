import os, shutil, tempfile, unittest, zipfile
from altui_tool import fixtures, inputs
from altui_tool.i18n import tr


class Resolve(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        self.tmp = os.path.join(self.d, "tmp"); os.makedirs(self.tmp)
        self.pak = fixtures.body_pak(os.path.join(self.d, "SlimBody_P.pak"))

    def zip_of(self, members):
        z = os.path.join(self.d, "mod.zip")
        with zipfile.ZipFile(z, "w") as zf:
            for name in members:
                zf.write(self.pak, name)
        return z

    def never(self, names):
        raise AssertionError("asked for %s" % names)

    def test_pak_is_itself(self):
        self.assertEqual(inputs.resolve(self.pak, self.never, None), self.pak)

    def test_zip_with_one_pak(self):
        out = inputs.resolve(self.zip_of(["Mod/Paks/SlimBody_P.pak", "readme.txt"]), self.never, self.tmp)
        self.assertEqual(out, os.path.join(self.tmp, "SlimBody_P.pak"))
        with open(out, "rb") as a, open(self.pak, "rb") as b:
            self.assertEqual(a.read(), b.read())

    def test_zip_with_several_asks(self):
        asked = []
        out = inputs.resolve(self.zip_of(["a/One_P.pak", "b/Two_P.pak"]), lambda n: asked.append(n) or n[1], self.tmp)
        self.assertEqual(asked, [["a/One_P.pak", "b/Two_P.pak"]])
        self.assertEqual(out, os.path.join(self.tmp, "Two_P.pak"))

    def test_zip_choice_cancelled(self):
        self.assertIsNone(inputs.resolve(self.zip_of(["a/One_P.pak", "b/Two_P.pak"]), lambda n: None, self.tmp))

    def test_zip_without_pak(self):
        z = os.path.join(self.d, "empty.zip")
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("readme.txt", "hi")
        with self.assertRaises(inputs.InputError) as c:
            inputs.resolve(z, self.never, self.tmp)
        self.assertEqual(str(c.exception), tr("input.no_pak"))

    def test_bad_zip(self):
        z = os.path.join(self.d, "bad.zip")
        with open(z, "wb") as f:
            f.write(b"nope")
        with self.assertRaises(inputs.InputError) as c:
            inputs.resolve(z, self.never, self.tmp)
        self.assertEqual(str(c.exception), tr("input.bad_zip"))

    def test_other_type(self):
        with self.assertRaises(inputs.InputError) as c:
            inputs.resolve(os.path.join(self.d, "mod.7z"), self.never, self.tmp)
        self.assertEqual(str(c.exception), tr("input.bad_type"))
