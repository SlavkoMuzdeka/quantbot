import pickle


def save_file(path, file):
    try:
        with open(path, "wb") as fp:
            pickle.dump(file, fp)
    except Exception as ex:
        print(f"An error occurs while saving file - {ex}")


def load_file(path):
    try:
        with open(path, "rb") as fp:
            file = pickle.load(fp)
        return file
    except Exception as ex:
        print(f"An error occurs while loading file - {ex}")
