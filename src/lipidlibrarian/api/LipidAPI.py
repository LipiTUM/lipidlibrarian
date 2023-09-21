import datetime
from importlib.metadata import version

import requests
# from ratelimit import limits, sleep_and_retry

from ..lipid.Adduct import Adduct
from ..lipid.Lipid import Lipid
from ..lipid.Nomenclature import Level


TIMEOUT_SECONDS = 120


class LipidAPI():
    # RATE_LIMIT_INTERVAL = 1
    # RATE_LIMIT_MAX_CALLS_PER_INTERVAL = 1000

    def __init__(self):
        """
        Initializes the API by reading in necessary data files, opening connections to databases
        and setting a user agent and timeout in case the API implements rate limiting.
        """
        self.data = []
        self.last_query = datetime.datetime.fromtimestamp(0)
        self.session: requests.Session = requests.Session()
        self.session.headers.update({
            'User-Agent': (f"Lipid Librarian Python Package @ LipiTUM / "
                           f"Version {version('lipidlibrarian')} <lipidlibrarian@lipitum.de>"),
            'From': 'lipidlibrarian@lipitum.de'
        })

    def query(self, query_parameters: Lipid | tuple[float, float, list[Adduct]], cutoff: int = 0) -> list[Lipid]:
        """
        Query the API. The method decides how the query parameters are interpreted. If you want more control
        over this, you may choose to use query_lipid(), query_mz(), query_id() or query_name() directly.

        This function may not be implemented in every database, and, if so, always returns empty lists.

        Parameters
        ----------
        query_parameters : Lipid
            The lipid object of which all usable information is queried and merged onto or turned into
            more Lipid objects.
        cutoff : int
            Maximum number of results the query returns. Only relevant for mz queries.

        Returns
        -------
        list[Lipid]
            A list of lipid objects that match the query.
        """
        if isinstance(query_parameters, Lipid):
            return self.query_lipid(query_parameters)
        return self.query_mz(*query_parameters, cutoff=cutoff)

    def query_lipid(self, lipid: Lipid) -> list[Lipid]:
        """
        Query the API with a Lipid object.

        This function may not be implemented in every database, and, if so, always returns empty lists.

        Parameters
        ----------
        lipid : Lipid
            The lipid object of which all usable information is queried and merged onto or turned into
            more Lipid objects.

        Returns
        -------
        list[Lipid]
            A list of lipid objects that match the query.
        """
        return []

    def query_mz(self, mz: float, tolerance: float, adducts: list[Adduct], cutoff: int = 0) -> list[Lipid]:
        """
        Query the API with a mass to charge ratio, tolerance and optionally polarity and adduct.

        This function may not be implemented in every database, and, if so, always returns empty lists.

        Parameters
        ----------
        mz : float
            Mass to charge ratio of the target lipid.
        tolerance : float
            Tolerance of the mass to charge ratio.
        adducts : list[Adduct]
            List of adducts which to search for.
        cutoff : int
            Maximum number of results the query returns

        Returns
        -------
        list[Lipid]
            A list of lipid objects that match the query with only the sensible fields filled.
        """
        return []

    def query_id(self, identifier: str) -> list[Lipid]:
        """
        Query the API with a database identifier.

        This function may not be implemented in every database, and, if so, always returns empty lists.

        Parameters
        ----------
        identifier : str
            The database identifier as a string.

        Returns
        -------
        list[Lipid]
            A list of lipid objects that match the query with only the sensible fields filled.
        """
        return []

    def query_name(self, name: str, level: Level = None) -> list[Lipid]:
        """
        Query the API with a lipid name. Optionally a level indicator may be supplied,
        so only relevant lipids of the same level are returned.

        This function may not be implemented in every database, and, if so, always returns empty lists.

        Parameters
        ----------
        name : str
            The name of the lipid.
        level : str
            The level of the lipid name. This value offers the choices of
            ('max', 'sum species', 'molecular subspecies', 'structural subspecies' or 'isomeric subspecies')
            and is assumed to be 'max' if none is specified.

        Returns
        -------
        list[Lipid]
            A list of lipid objects that match the query with only the sensible fields filled.
        """
        return []

    # @sleep_and_retry
    # @limits(calls=RATE_LIMIT_MAX_CALLS_PER_INTERVAL, period=RATE_LIMIT_INTERVAL)
    def execute_http_query(self, url: str, timeout: int = 30) -> requests.Response:
        """
        Query the API via a http request with respect to the rate limiting values set as constants.

        Parameters
        ----------
        url : str
            The http query to be sent.
        timeout : int
            Seconds, after which the request is killed.

        Returns
        -------
        requests.Response
            The unmodified Response object with status code and result text.
        """
        try:
            response = self.session.get(url, timeout=timeout)
            if response is None:
                # If there is no connection to the internet lots of APIs have issues (relatable).
                # Return a dummy response with 'server error' as status code to handle them here.
                response = requests.Response()
                response.status_code = 503
            return response
        except (TimeoutError, requests.RequestException, KeyError, IndexError, TypeError) as _:
            # If there is no connection to the internet lots of APIs have issues (relatable).
            # Return a dummy response with 'server error' as status code to handle them here.
            response = requests.Response()
            response.status_code = 503
            return response
        
