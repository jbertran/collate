"""
A minimalist PDF file collation utility.

Because Python doesn't have a lot in the way of collating PDFs together,
this is by default a GhostScript wrapper that takes a JSON dict representing
the directory structure targeted by collation.
"""

import argparse
import json
import pathlib
import subprocess


def expand_path_rec(path_holder, path_prefix):
    """Recursively expand a path dict.

    Arguments:
      - path_holder: a dict or list of path information
      - path_prefix: the prefix to use for final path generation

    Returns: a list of pathlib.Path instances
    """
    if isinstance(path_holder, dict):
        sub_expands = [
            expand_path_rec(v, path_prefix/pathlib.Path(k)) for k, v in path_holder.items()
        ]
        return [path for path_list in sub_expands for path in path_list]
    if isinstance(path_holder, list):
        paths = []
        for item in (pathlib.Path(p) for p in path_holder):
            if isinstance(item, dict):
                paths.extend(expand_path_rec(item, path_prefix))
            else:
                paths.append(path_prefix/item)
        return paths
    raise Exception(
        'Expected str, dict or list, got {}'.format(type(path_holder))
    )


def expand_path_data(path_data, path_base):
    """Expand path data and verify it.

    Arguments:
      - path_holder: a dict or list of path information
      - path_prefix: the prefix to use for final path generation

    Returns: a string of space-separated file paths, if all paths exists.
    """
    paths = expand_path_rec(path_data, path_base)
    errors = [str(path) for path in paths if not path.is_file()]
    if errors:
        raise Exception(
            'Missing files: \n\t{}'.format('\n\t'.join(errors))
        )
    return paths


def execute(input_files, output_file, papersize):
    """Run the command specified with the correct input/output."""
    command_args = [
        'gs',
        '-dBATCH',
        '-dNOPAUSE',
        '-q',
        '-sDEVICE=pdfwrite',
        '-dAutoRotatePages=/None',
        '-sOutputFile={output}'.format(output=output_file)
    ]

    if papersize is not None:
        command_args.append('-sPAPERSIZE={}'.format(papersize))

    subprocess.run(command_args + [str(path) for path in input_files])


def prepare_parser():
    """Prepare the CLI parser."""
    parser = argparse.ArgumentParser(
        description='Collate PDFs from a directory description using GS'
    )
    parser.add_argument(
        '--papersize',
        help="""Target paper size for the collated document.
        This should be a paper size known by GhostScript""",
        default='a4'
    )
    parser.add_argument(
        '-c', '--context',
        help='Directory tree base path',
        type=pathlib.Path,
        default=pathlib.Path('.')
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--data', help='Files as a JSON string')
    group.add_argument(
        '-f', '--file',
        help='Files as described by a JSON file',
        dest='data_file'
    )
    parser.add_argument(
        '-o', '--output', help='Output file', default='collate.out'
    )
    return parser


def load_data(args):
    if args.data:
        data = json.loads(
            args.data)
    else:
        with open(args.data_file, 'r') as data_file:
            data = json.load(
                data_file)
    return data


def parse_cli():
    """Parse the CLI and execute the collation."""
    parser = prepare_parser()
    args = parser.parse_args()
    data = load_data(args)

    input_list = expand_path_data(data, args.context)

    execute(input_list, args.output, None)


if __name__ == '__main__':
    parse_cli()
