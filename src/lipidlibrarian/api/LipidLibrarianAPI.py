import logging
import re

from rdkit import Chem

from .LipidAPI import LipidAPI
from ..lipid.Lipid import Lipid
from ..lipid.Nomenclature import Level
from ..lipid.Source import Source
from ..lipid.StructureIdentifier import StructureIdentifier


phosphocholines = {
    "PA": ("InChI=1S/C3H7O6P/c4-1-3(5)2-9-10(6,7)8/h3H,1-2H2,(H2,6,7,8)/q-2/t3-/m1/s1,", 3, 4),
    "PE": ("InChI=1S/C5H12NO6P/c6-1-2-11-13(9,10)12-4-5(8)3-7/h5H,1-4,6H2,(H,9,10)/q-2/t5-/m1/s1", 6, 7),
    "PC": ("InChI=1S/C8H19NO6P/c1-9(2,3)4-5-14-16(12,13)15-7-8(11)6-10/h8H,4-7H2,1-3H3,(H,12,13)/q-1/p-1/t8-/m1/s1", 9, 10),
    "PG": ("InChI=1S/C6H13O8P/c7-1-5(9)3-13-15(11,12)14-4-6(10)2-8/h5-7,9H,1-4H2,(H,11,12)/q-2/t5-,6-/m0/s1", 7, 9),
    "PS": ("InChI=1S/C6H12NO8P/c7-5(6(10)11)3-15-16(12,13)14-2-4(9)1-8/h4-5H,1-3,7H2,(H,10,11)(H,12,13)/q-2/t4-,5-/m1/s1", 7, 8),
    "LPA": ("InChI=1S/C3H7O6P/c4-1-3(5)2-9-10(6,7)8/h3H,1-2H2,(H2,6,7,8)/q-2/t3-/m1/s1,", 3, 4),
    "LPE": ("InChI=1S/C5H12NO6P/c6-1-2-11-13(9,10)12-4-5(8)3-7/h5H,1-4,6H2,(H,9,10)/q-2/t5-/m1/s1", 6, 7),
    "LPC": ("InChI=1S/C8H19NO6P/c1-9(2,3)4-5-14-16(12,13)15-7-8(11)6-10/h8H,4-7H2,1-3H3,(H,12,13)/q-1/p-1/t8-/m1/s1", 9, 10),
    "LPG": ("InChI=1S/C6H13O8P/c7-1-5(9)3-13-15(11,12)14-4-6(10)2-8/h5-7,9H,1-4H2,(H,11,12)/q-2/t5-,6-/m0/s1", 7, 9),
    "LPS": ("InChI=1S/C6H12NO8P/c7-5(6(10)11)3-15-16(12,13)14-2-4(9)1-8/h4-5H,1-3,7H2,(H,10,11)(H,12,13)/q-2/t4-,5-/m1/s1", 7, 8)
}


def validate_double_bonds(double_bonds: list[int] | list[str]) -> list[tuple[int, str]]:
    validated_double_bonds = []

    for double_bond in list(set(map(str, double_bonds))):
        position, direction = (int(double_bond[0:-1]), double_bond[-1]) if double_bond[-1] in ['Z', 'E'] else (int(double_bond), '')
        validated_double_bonds.append((position, direction))

    validated_double_bonds = sorted(validated_double_bonds)

    last_position = 0
    last_direction = 'E'
    for double_bond in validated_double_bonds:
        if last_direction == 'E' and double_bond[0] == last_position + 1:
            raise ValueError("An 'E' double bond directly after another is not possible in fatty acid chains.")
        elif last_direction == 'Z' and double_bond[0] <= last_position + 2:
            raise ValueError("A 'Z' double bond directly after another is not possible in fatty acid chains.")
        last_position = double_bond[0]
        last_direction = double_bond[1]

    return validated_double_bonds


def generate_fatty_acid(length: int, double_bonds: list[int] | list[str]):
    if len == 0:
        return 'OH'

    fatty_acid = 'O=[C-]'
    index = 1

    for double_bond in validate_double_bonds(double_bonds):
        position, direction = double_bond
        if position >= length -1:
            raise ValueError(f"Double bond position { position } is invalid in a fatty acid of length { length }.")

        fatty_acid = fatty_acid + ('C' * (position - index - 1)) + "\\C=C" + ("/" if direction == 'Z' else "\\")
        index = position + 1
    fatty_acid = fatty_acid + ('C' * (length - index))
    fatty_acid = fatty_acid.replace('//', '/')

    return Chem.MolFromSmiles(fatty_acid)


def create_phospchocholine(lipid_class: str, fatty_acid_sn1_length: int, fatty_acid_sn1_double_bonds: list[int] | list[str], fatty_acid_sn2_length: int, fatty_acid_sn2_double_bonds: list[int] | list[str]) -> Chem.Mol:
    head_group = Chem.MolFromInchi(phosphocholines[lipid_class][0])
    head_group_bond_atom1 = head_group.GetAtomWithIdx(phosphocholines[lipid_class][1])
    head_group_bond_atom1.SetFormalCharge(0)
    head_group_bond_atom1.UpdatePropertyCache()
    head_group_bond_atom2 = head_group.GetAtomWithIdx(phosphocholines[lipid_class][2])
    head_group_bond_atom2.SetFormalCharge(0)
    head_group_bond_atom2.UpdatePropertyCache()

    fatty_acid_sn1 = generate_fatty_acid(fatty_acid_sn1_length, fatty_acid_sn1_double_bonds)
    fatty_acid_sn1_bond_atom = fatty_acid_sn1.GetAtomWithIdx(1)
    fatty_acid_sn1_bond_atom.SetFormalCharge(0)
    fatty_acid_sn1_bond_atom.UpdatePropertyCache()
    fatty_acid_sn2 = generate_fatty_acid(fatty_acid_sn2_length, fatty_acid_sn2_double_bonds)
    fatty_acid_sn2_bond_atom = fatty_acid_sn2.GetAtomWithIdx(1)
    fatty_acid_sn2_bond_atom.SetFormalCharge(0)
    fatty_acid_sn2_bond_atom.UpdatePropertyCache()

    m1_2 = Chem.CombineMols(head_group, fatty_acid_sn1)
    m1_2 = Chem.EditableMol(m1_2)
    m1_2.AddBond(phosphocholines[lipid_class][1], max(range(head_group.GetNumAtoms())) + 2, order=Chem.rdchem.BondType.SINGLE)
    m1_2 = m1_2.GetMol()

    m1_2_3 = Chem.CombineMols(m1_2, fatty_acid_sn2)
    m1_2_3 = Chem.EditableMol(m1_2_3)
    m1_2_3.AddBond(phosphocholines[lipid_class][2], max(range(m1_2.GetNumAtoms())) + 2, order=Chem.rdchem.BondType.SINGLE)
    m1_2_3 = m1_2_3.GetMol()

    return m1_2_3


class LipidLibrarianAPI(LipidAPI):

    def query_lipid(self, lipid: Lipid) -> list[Lipid]:
        if lipid.nomenclature.lipid_class_abbreviation in phosphocholines.keys() and lipid.nomenclature.level == Level.isomeric_lipid_species:
            fatty_acid_sn1_length = int(lipid.nomenclature.residues[0].split(':')[0])
            fatty_acid_sn2_length = int(lipid.nomenclature.residues[1].split(':')[0])

            double_bonds = [x for x in re.split('\(|\)|:|,|/', lipid.nomenclature.name) if 'E' in x or 'Z' in x]

            fatty_acid_sn1_double_bond_amount = int(lipid.nomenclature.residues[0].split(':')[1])

            fatty_acid_sn1_double_bonds = double_bonds[:fatty_acid_sn1_double_bond_amount] if fatty_acid_sn1_length > 0 else []
            fatty_acid_sn2_double_bonds = double_bonds[fatty_acid_sn1_double_bond_amount:] if fatty_acid_sn2_length > 0 else []

            logging.info(f"LipidLibrarianAPI: Creating phosphocholine of input {lipid.nomenclature.name} with:\n\tclass: {lipid.nomenclature.lipid_class_abbreviation}\n\tresidues: {lipid.nomenclature.residues[0]}\n\tsn1 length: {fatty_acid_sn1_length}\n\tsn1 dbs: {fatty_acid_sn1_double_bonds}\n\tsn2 length: {fatty_acid_sn2_length}\n\tsn2 dbs: {fatty_acid_sn2_double_bonds}")

            lipid_mol = create_phospchocholine(
                lipid.nomenclature.lipid_class_abbreviation,
                fatty_acid_sn1_length,
                fatty_acid_sn1_double_bonds,
                fatty_acid_sn2_length,
                fatty_acid_sn2_double_bonds
            )

            source = Source(lipid.nomenclature.name, Level.isomeric_lipid_species, 'lipidlibrarian')

            lipid.nomenclature.add_structure_identifier(StructureIdentifier.from_data(
                Chem.MolToSmiles(lipid_mol),
                'smiles',
                source
            ))

            lipid.nomenclature.add_structure_identifier(StructureIdentifier.from_data(
                Chem.inchi.MolToInchi(lipid_mol),
                'inchi',
                source
            ))

            lipid.nomenclature.add_structure_identifier(StructureIdentifier.from_data(
                Chem.inchi.MolToInchiKey(lipid_mol),
                'inchikey',
                source
            ))

        return [lipid]
