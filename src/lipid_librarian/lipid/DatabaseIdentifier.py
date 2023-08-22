from typing import Iterable

from .Nomenclature import Level
from .Source import Source


class DatabaseIdentifier():

    def __init__(self) -> None:
        self.database: str | None = None
        self.identifier: str | None = None
        self.sources: set[Source] = set()

    @classmethod
    def from_data(cls, database: str, identifier: str, source: Source):
        obj = cls()
        obj.database = database
        obj.identifier = str(identifier)
        obj.add_source(source)
        return obj

    @property
    def url(self) -> str | None:
        if self.database is None or self.identifier is None:
            return None

        if self.database == 'alex123':
            for source in self.sources:
                if source.source == 'alex123':
                    if source.lipid_level >= Level.molecular_lipid_species:
                        return (f"http://alex123.info/ALEX123/MS2.php"
                                f"?type=MS2.php&ms={source.lipid_name.replace(' ', '%20')}"
                                f"&mstol=0.0100&mswin=0.0000&mscharge=1&adduct=50&ms2=&"
                                f"ms2tol=0.0100&ms2win=0.0000&submit_name=Submit"
                        )
                    elif source.lipid_level >= Level.sum_lipid_species:
                        return (f"http://alex123.info/ALEX123/MS.php"
                                f"?type=MS.php&class=9999&ms={source.lipid_name.replace(' ', '%20')}"
                                f"&mstol=0.0100&mswin=0.0000&mscharge=50&adduct=50&submit_name=Submit"
                        )
        elif self.database == 'lipidmaps':
            return f"https://lipidmaps.org/databases/lmsd/{self.identifier}"
        elif self.database == 'swisslipids':
            return f"http://www.swisslipids.org/#/entity/{self.identifier}"
        elif self.database == 'hmdb':
            return f"https://hmdb.ca/metabolites/{self.identifier}"
        elif self.database == 'pubchem':
            return f"https://pubchem.ncbi.nlm.nih.gov/compound/{self.identifier}"
        elif self.database == 'chebi':
            if self.identifier.startswith('CHEBI:'):
                return f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={self.identifier}"
            else:
                return f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:{self.identifier}"
        elif self.database == 'rhea':
            if self.identifier.startswith('RHEA:'):
                return f"https://www.rhea-db.org/rhea/{self.identifier[5:]}"
            else:
                return f"https://www.rhea-db.org/rhea/{self.identifier}"
        elif self.database == 'reactome':
            return f"https://reactome.org/content/detail/{self.identifier}"
        elif self.database == 'kegg':
            return f"https://www.kegg.jp/entry/{self.identifier}"
        elif self.database == 'wikipathways':
            return f"https://www.wikipathways.org/pathways/{self.identifier}.html"
        elif self.database == 'uniprotkb':
            return f"https://www.uniprot.org/uniprotkb/{self.identifier}/entry"
        elif self.database == 'metanetx':
            return f"https://www.metanetx.org/chem_info/{self.identifier}"
        else:
            return ""

    def add_source(self, source: Source) -> None:
        self.sources.add(source)

    def add_sources(self, sources: Iterable[Source]) -> None:
        for source in sources:
            self.add_source(source)

    def merge(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise ValueError((
                f"Source and target cannot be merged, since they do not inherit from the same instance: "
                f"{type(self)} and {type(other)}."
            ))

        if self.database != other.database or self.identifier != other.identifier:
            return False

        self.add_sources(other.sources)
        return True

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return f"{self.identifier}"
