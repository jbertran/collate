"""
A minimalist file collation utility aimed at obscure CLI commands.

Because Python doesn't have a lot in the way of collating PDFs together,
this is by default a `pdftk` wrapper that takes a JSON dict representing
the directory structure targeted by collation.
"""

import argparse
import collections
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
            expand_path_rec(v, path_prefix/k) for k, v in path_holder.items()
        ]
        return [path for path_list in sub_expands for path in path_list]
    if isinstance(path_holder, list):
        paths = []
        for item in path_holder:
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
    return ' '.join(str(path) for path in paths)


def execute(template, input_files, output_file):
    """Run the command specified with the correct input/output."""
    command = template.format(input=input_files, output=output_file)
    subprocess.run(command)


def prepare_parser():
    """Prepare the CLI parser."""
    parser = argparse.ArgumentParser(
        description='Collate PDFs from a directory tree'
    )
    parser.add_argument(
        '--command',
        help='Command format collate pdfs, with `output` and `input` variables',
        default='pdftk {input} cat output {output}'
    )
    parser.add_argument(
        '-p', '--path',
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


def parse_cli():
    """Parse the CLI and execute the collation."""
    parser = prepare_parser()
    args = parser.parse_args()
    if args.data:
        data = json.loads(args.data, object_pairs_hook=collections.OrderedDict)
    else:
        with open(args.data_file, 'r') as data_file:
            data = json.load(
                data_file, object_pairs_hook=collections.OrderedDict
            )
    try:
        input_path_str = expand_path_data(data, args.path)
    except Exception as exc:
        print(str(exc))
        exit(1)
    result = execute(args.command, input_path_str, args.output)


if __name__ == '__main__':
    parse_cli()
