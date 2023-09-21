import argparse as ap
import logging
import os
import pathlib
import sys
from importlib.metadata import version

from .LipidQuery import LipidQuery


def main(parser=ap.ArgumentParser()):
    parser.add_argument(
        "--version",
        action="store_true",
        help="Shows the app version."
    )
    parser.add_argument(
        "--sql",
        action="store_true",
        help="Use a SQL server to query ALEX123 data."
    )
    parser.add_argument(
        "--sql-host",
        type=str,
        default="localhost",
        help=""
    )
    parser.add_argument(
        "--sql-port",
        type=int,
        default=3306,
        help=""
    )
    parser.add_argument(
        "--sql-user",
        type=str,
        help=""
    )
    parser.add_argument(
        "--sql-password",
        type=str,
        help=""
    )
    parser.add_argument(
        "--sql-database",
        type=str,
        default="ALEX123",
        help=""
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print out verbose information to stdout."
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=['text', 'json', 'html'],
        default='json',
        help="Specify the output format."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help=(
            "Specify the output directory. If this option is not set, the results will be printed out "
            "to stdout as one line per lipid. Keep in mind, that if -v is activated simultaneously, both "
            "the verbose logging information and the results will be printed to stdout."
        )
    )
    parser.add_argument(
        "--cutoff",
        type=int,
        default=0,
        help="Cutoff the idividual mz query results from the apis, so the output doesn't get too large."
    )
    parser.add_argument(
        "--requery",
        type=int,
        default=0,
        help="Number of times lipid librarian will requery the APIs with the results to enhance them."
    )
    parser.add_argument(
        'lipids',
        metavar='L',
        type=str,
        nargs='*',
        default=(None if sys.stdin.isatty() else sys.stdin),
        help=(
            'Lipids to search for. A lipid can either be a name, like "PLPE", a scientific name like "PC(18:1_20:0)",'
            ' or the mass to charge value with tolerance and either adduct or polarity like "410.243;0.001;+H+,+Na+" '
            'or "410.243;0.001;pos". You can pass in multiple lipids in quotation marks seperated by spaces, or plain'
            ' text files with one lipid per line.'
        )
    )

    args = parser.parse_args()

    if args.version:
        print(version('lipidlibrarian'))
        exit(0)

    if args.verbose:
        # Configure logs
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(logging.Formatter(
            '%(asctime)s\t[%(levelname)s]\t%(name)s:\t%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root.addHandler(stdout_handler)

    # Check if ALEX123 should use an SQL database
    sql_args: dict = {}
    if args.sql:
        sql_args = {
            'host': args.sql_host,
            'port': args.sql_port,
            'user': args.sql_user,
            'password': args.sql_password,
            'database': args.sql_database,
        }

    file_extension = ''
    if args.output is not None:
        logging.info(f"CLI: Creating directory {os.getcwd()}/{args.output}.")
        pathlib.Path(args.output).mkdir(parents=True, exist_ok=True)
        if args.output_format == 'json':
            file_extension = 'json'
        elif args.output_format == 'html':
            file_extension = 'html'
        else:
            file_extension = 'txt'

    if args.lipids is None:
        exit(0)
    else:
        # Generate Lipid objects
        for val in args.lipids:
            lipid_file = True
            try:
                with open(val, 'r') as file:
                    for line in file.readlines():
                        lipid_query = LipidQuery(
                            line.rstrip(),
                            requeries=args.requery,
                            cutoff=args.cutoff,
                            sql_args=sql_args
                        )
                        lipid_query.query()
                        for lipid in lipid_query.lipids:
                            if args.output is not None:
                                with open(f"{args.output}/{repr(lipid).replace('/', '+')}", 'w') as output_file:
                                    output_file.write(format(lipid, args.output_format))
                            else:
                                print(format(lipid, args.output_format))
            except FileNotFoundError as _:
                lipid_file = False

            if not lipid_file:
                lipid_query = LipidQuery(
                    val.rstrip(),
                    requeries=args.requery,
                    cutoff=args.cutoff,
                    sql_args=sql_args
                )
                lipids = lipid_query.query()
                for lipid in lipids:
                    if args.output is not None:
                        with open(f"{args.output}/{repr(lipid).replace('/', '+')}.{file_extension}", 'w') as output_file:
                            output_file.write(format(lipid, args.output_format))
                    else:
                        print(format(lipid, args.output_format))
