import os
def create_directory_for_path(path):
    print(path)
    dirname = os.path.dirname(path)
    print(dirname)

    if os.path.exists(dirname) and not os.path.exists(path):
        print("Creating")
        os.makedirs(path)
        return

    if not dirname:
        dirname = path
        print(dirname)

    if os.path.exists(dirname):
        print("Exists - exiting")
        return
    print("Creating")
    os.makedirs(dirname)
