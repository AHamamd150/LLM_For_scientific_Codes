import tempfile
import unittest
from pathlib import Path

from code_generator.executor import execute_python


class ExecutorTests(unittest.TestCase):
    def test_executes_generated_python_in_output_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "analysis.py"
            script.write_text(
                "from pathlib import Path\n"
                "Path('created.txt').write_text('ok')\n"
                "print('done')\n",
                encoding="utf-8",
            )
            output = root / "output"
            output.mkdir()
            result = execute_python(
                script,
                [],
                working_directory=output,
            )
            self.assertTrue(result.succeeded)
            self.assertEqual(result.stdout.strip(), "done")
            self.assertEqual(
                (output / "created.txt").read_text(encoding="utf-8"),
                "ok",
            )


if __name__ == "__main__":
    unittest.main()
