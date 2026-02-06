from lipidlibrarian.lipid.Nomenclature import Level


LIPID_NAME_TEST_MATRIX = {
    "PC": {
        Level.sum_lipid_species: {
            "name": "PC 38:1",
            "expects": {
                "has_fragments": False,
            },
        },
        Level.molecular_lipid_species: {
            "name": "PC 18:1_20:0",
            "expects": {
                "has_fragments": True,
            },
        },
        Level.structural_lipid_species: {
            "name": "PC 18:1/20:0",
            "expects": {
                "has_fragments": True,
            },
        },
        Level.isomeric_lipid_species: {
            "name": "PC 18:1(9Z)/20:0",
            "expects": {
                "has_fragments": True,
            },
        },
    },
    "PE": {
        Level.sum_lipid_species: {
            "name": "PE 36:2",
            "expects": {
                "has_fragments": False,
            },
        },
        Level.molecular_lipid_species: {
            "name": "PE 18:0_18:2",
            "expects": {
                "has_fragments": True,
            },
        },
        Level.structural_lipid_species: {
            "name": "PE 18:0/18:2",
            "expects": {
                "has_fragments": True,
            },
        },
        Level.isomeric_lipid_species: {
            "name": "PE 18:0/18:1(9Z)",
            "expects": {
                "has_fragments": True,
            },
        },
    },
    "PS": {
        Level.sum_lipid_species: {
            "name": "PS 36:1",
            "expects": {
                "has_fragments": False,
            },
        },
        Level.molecular_lipid_species: {
            "name": "PS 18:0_18:1",
            "expects": {
                "has_fragments": True,
            },
        },
        Level.structural_lipid_species: {
            "name": "PS 18:0/18:1",
            "expects": {
                "has_fragments": True,
            },
        },
        Level.isomeric_lipid_species: {
            "name": "PS 18:0/18:1(9Z)",
            "expects": {
                "has_fragments": True,
            },
        },
    },
    "ST 27:1;O": {
        Level.isomeric_lipid_species: {
            "name": "ST 27:1;O",
            "expects": {
                "has_fragments": True,
            },
        },
    },
    "ST 27:1": {
        Level.structural_lipid_species: {
            "name": "ST 27:1/18:1",
            "expects": {
                "has_fragments": True,
            },
        },
    },
    "Cer": {
        Level.sum_lipid_species: {
            "name": "Cer 36:1;O2",
            "expects": {
                "has_fragments": True,
            },
        },
        Level.structural_lipid_species: {
            "name": "Cer 18:1;O2/20:0",
            "expects": {
                "has_fragments": True,
            },
        },
        Level.isomeric_lipid_species: {
            "name": "Cer 18:1;O2/20:1(11Z)",
            "expects": {
                "has_fragments": True,
            },
        },
    },
    "TG": {
        Level.sum_lipid_species: {
            "name": "TG 54:2",
            "expects": {
                "has_fragments": False,
            },
        },
        Level.molecular_lipid_species: {
            "name": "TG 16:1_18:1_20:0",
            "expects": {
                "has_fragments": True,
            },
        },
        Level.structural_lipid_species: {
            "name": "TG 16:1/18:1/20:0",
            "expects": {
                "has_fragments": True,
            },
        },
        Level.isomeric_lipid_species: {
            "name": "TG 16:1(9Z)/18:1(9Z)/20:0",
            "expects": {
                "has_fragments": True,
            },
        },
    },
}
