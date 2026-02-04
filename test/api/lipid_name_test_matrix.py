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
            "name": "PE 18:0/18:1(9Z,11Z)",
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
}
