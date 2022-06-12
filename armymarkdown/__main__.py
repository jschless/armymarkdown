import os
import sys


from . import memo_model
from . import writer


def main():
    print("usage:  [file_path]")
    m = memo_model.parse(os.path.join(os.getcwd(), sys.argv[1]))
    print(m)
    mw = writer.MemoWriter(m)
    mw.write()
    mw.generate_memo()


if __name__ == "__main__":
    main()
