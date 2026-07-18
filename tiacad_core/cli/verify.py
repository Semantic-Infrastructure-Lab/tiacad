"""`tiacad verify` — evaluate a model's embedded expect: contract."""

import json
import traceback
from pathlib import Path

from .output import print_error, print_success


def cmd_verify(args):
    """
    Evaluate a model's embedded expect: contract and report the result.

    Single-purpose sibling of `check --contract`: no part-by-part dimension
    table, just the contract verdict — a concise console summary plus,
    with --json, a machine-readable result for CI/tooling consumption.
    Implements docs/developer/MODEL_VALIDATION.md "Best Next Improvements" #3.
    """
    from ..parser.tiacad_parser import TiaCADParser
    from ..testing.contracts import ContractError, check_contract

    input_file = Path(args.input)
    if not input_file.exists():
        print_error(f"File not found: {input_file}")
        return 1

    try:
        doc = TiaCADParser.parse_file(str(input_file))
        result = check_contract(doc)
    except ContractError as e:
        print_error(f"{input_file.name}: {e}")
        if args.json:
            print(json.dumps({'file': str(input_file), 'error': str(e)}, indent=2, sort_keys=True))
        return 1
    except Exception as e:
        print_error(f"Verify failed: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        return 1

    if result.ok:
        print_success(result.summary())
    else:
        print_error(result.summary())

    if args.json:
        print(json.dumps({
            'file': str(input_file),
            'ok': result.ok,
            'part_name': result.part_name,
            'violations': [
                {'check': v.check, 'message': v.message} for v in result.violations
            ],
        }, indent=2, sort_keys=True))

    return 0 if result.ok else 1
