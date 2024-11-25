import json
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


def load_config(config_path):
    try:
        with open(config_path, "rb") as f:
            return json.load(f)
    except Exception as ex:
        print(f"Error while loading config - {ex}")
        raise


def save_config(config, config_path):
    try:
        with open(config_path, "wb") as f:
            json.dump(config, f, indent=4)
    except Exception as ex:
        print(f"Error while saving config - {ex}")
        raise
