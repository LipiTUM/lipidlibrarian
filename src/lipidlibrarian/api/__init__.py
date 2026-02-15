from .Alex123API import Alex123API
from .LinexAPI import LinexAPI
from .LipidAPI import LipidAPI
from .LipidMapsAPI import LipidMapsAPI
from .LionAPI import LionAPI
from .LipidLibrarianAPI import LipidLibrarianAPI
from .SwissLipidsAPI import SwissLipidsAPI


# Initialize all API instances here, so connections to databases,
# data files and other intense __init__ tasks are executed only once
# when the package is imported. If you don't want to initialize all
# APIs you should consider importing the APIs directly and instantiating
# them yourself.

API_REGISTRY: dict[str, type[LipidAPI]] = {
    'alex123': Alex123API,
    'linex': LinexAPI,
    'lipidmaps': LipidMapsAPI,
    'lion': LionAPI,
    'lipidlibrarian': LipidLibrarianAPI,
    'swisslipids': SwissLipidsAPI,
}

_API_CACHE: dict[str, LipidAPI] = {}

supported_APIs = frozenset(API_REGISTRY.keys())


def init_APIs(which_APIs: set[str] = supported_APIs, sql_args: dict | None = None) -> dict[str, LipidAPI]:

    apis: dict[str, LipidAPI] = {}

    for name in which_APIs:
        api_cls = API_REGISTRY[name]

        if name not in _API_CACHE:
            if sql_args is not None and name == 'alex123':
                _API_CACHE[name] = api_cls(sql_args)
            else:
                _API_CACHE[name] = api_cls()

        apis[name] = _API_CACHE[name]

    return apis
