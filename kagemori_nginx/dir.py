import os
def create_directory_for_path(path):
    dirname = os.path.dirname(path)

    if os.path.exists(dirname) and not os.path.exists(path):
        os.makedirs(path)
        return

    if not dirname:
        dirname = path

    if os.path.exists(dirname):
        return

    os.makedirs(dirname)
