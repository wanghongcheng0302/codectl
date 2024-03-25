from operator import itemgetter

global_version = "v1.1.0"


def filter_upper(value: str):
    return value.upper()


def filter_apis(value):
    return filter(lambda x: itemgetter("version")(x) == "1.0.0", value)
