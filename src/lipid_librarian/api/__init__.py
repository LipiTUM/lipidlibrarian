import logging

from .Alex123API import Alex123API
from .LinexAPI import LinexAPI
from .LipidAPI import LipidAPI
from .LipidMapsAPI import LipidMapsAPI
from .LipidOntologyAPI import LipidOntologyAPI
from .SwissLipidsAPI import SwissLipidsAPI


# Initialize all API instances here, so connections to databases,
# data files and other intense __init__ tasks are executed only once
# when the package is imported. If you don't want to initialize all
# APIs you should consider importing the APIs directly and instantiating
# them yourself.

alex123_API = LipidAPI()
linex_API = LipidAPI()
lipid_maps_API = LipidAPI()
lipid_ontology_API = LipidAPI()
swiss_lipids_API = LipidAPI()

supported_APIs = frozenset(['alex123', 'linex', 'lipidmaps', 'lipidontology', 'swisslipids'])


def init_APIs(which_APIs: set[str] = supported_APIs, sql_args: dict = None) -> dict[str, LipidAPI]:
    global alex123_API
    global linex_API
    global lipid_maps_API
    global lipid_ontology_API
    global swiss_lipids_API

    if 'alex123' in which_APIs:
        if not isinstance(alex123_API, Alex123API):
            alex123_API = Alex123API(sql_args)
    else:
        alex123_API = LipidAPI()

    if 'linex' in which_APIs:
        if not isinstance(linex_API, LinexAPI):
            linex_API = LinexAPI()
    else:
        linex_API = LipidAPI()

    if 'lipidmaps' in which_APIs:
        if not isinstance(lipid_maps_API, LipidMapsAPI):
            lipid_maps_API = LipidMapsAPI()
    else:
        lipid_maps_API = LipidAPI()

    # if 'lipidontology' in which_APIs:
    #     if not isinstance(lipid_ontology_API, LipidOntologyAPI):
    #         lipid_ontology_API = LipidOntologyAPI()
    # else:
    logging.warn("Lipid Ontology is disabled for this version, please check for updates.")
    lipid_ontology_API = LipidAPI()

    if 'swisslipids' in which_APIs:
        if not isinstance(swiss_lipids_API, SwissLipidsAPI):
            swiss_lipids_API = SwissLipidsAPI()
    else:
        swiss_lipids_API = LipidAPI()

    return {
        'alex123': alex123_API,
        'linex': linex_API,
        'lipidmaps': lipid_maps_API,
        'lipidontology': lipid_ontology_API,
        'swisslipids': swiss_lipids_API
    }
