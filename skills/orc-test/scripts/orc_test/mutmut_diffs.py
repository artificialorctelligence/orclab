"""The diff `mutmut show <key>` prints, for many keys from one process: `key path` per stdin
line in, `# key` then that diff out. langs/python.py runs this from mutmut's own cwd, because one
`mutmut show` per survivor was ~75% of a real project's analyze (BACKLOG #42)."""

import sys

from mutmut.__main__ import Config, get_diff_for_mutant

Config.ensure_loaded()
for line in sys.stdin:
    key, path = line.split()
    print("#", key)
    try:
        print(get_diff_for_mutant(key, path=path))
    except Exception as e:      # one mutant mutmut can no longer show must not hide the rest
        print(f"{key}: {e}")
