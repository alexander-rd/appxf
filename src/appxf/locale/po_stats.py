# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""Statistics and analysis tools for gettext PO/POT files."""

import sys


def read_context_from_pot(pot_file):
    """Extract context tags from a POT file

    Args:
        pot_file: Path to the POT file

    Returns:
        set: All context tags found in the file
    """
    contexts = set()

    with open(pot_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("msgctxt "):
                # Extract context value
                context = line[8:].strip('"')
                contexts.add(context)

    return sorted(contexts)


def analyze_po_file(po_file):
    """Analyze a PO file and return translation statistics by context.

    Args:
        po_file: Path to the PO file

    Returns:
        dict: Statistics with context as key and dict with
        'translated' and 'total' counts
    """
    stats = {}
    current_context = None
    current_msgid = None
    in_msgstr = False
    msgstr_content = ""

    with open(po_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line.startswith("msgctxt "):
                current_context = line[8:].strip('"')

            elif line.startswith("msgid ") and current_context:
                current_msgid = line[6:].strip('"')

            elif line.startswith("msgstr ") and current_context and current_msgid:
                msgstr_content = line[7:].strip('"')
                in_msgstr = True

            elif in_msgstr and line.startswith('"'):
                # Continuation line for msgstr
                msgstr_content += line.strip('"')

            elif in_msgstr and not line.startswith('"'):
                # End of msgstr block
                if current_context not in stats:
                    stats[current_context] = {"translated": 0, "total": 0}

                stats[current_context]["total"] += 1
                if msgstr_content:
                    stats[current_context]["translated"] += 1

                current_context = None
                current_msgid = None
                in_msgstr = False
                msgstr_content = ""

    # Handle last entry if file ends in msgstr
    if in_msgstr and current_context:
        if current_context not in stats:
            stats[current_context] = {"translated": 0, "total": 0}

        stats[current_context]["total"] += 1
        if msgstr_content:
            stats[current_context]["translated"] += 1

    return stats


def get_incomplete_contexts(po_file):
    """Get contexts that are not fully translated.

    Args:
        po_file: Path to the PO file

    Returns:
        dict: Only contexts with incomplete translations
    """
    stats = analyze_po_file(po_file)
    incomplete = {
        ctx: data for ctx, data in stats.items() if data["translated"] < data["total"]
    }
    return incomplete


def print_contexts(pot_file):
    """Print all contexts from a POT file."""
    contexts = read_context_from_pot(pot_file)
    print(f"Contexts: {', '.join(contexts)}")


def print_incomplete(po_file):
    """Print incomplete contexts from a PO file."""
    incomplete = get_incomplete_contexts(po_file)
    if incomplete:
        print("Incomplete contexts:")
        for ctx, data in sorted(incomplete.items()):
            print(f"    {ctx}: {data['translated']}/{data['total']} translated")
    else:
        print("  All contexts fully translated")


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Statistics and analysis tools for gettext PO/POT files."
    )
    parser.add_argument("file", help="Path to PO or POT file")
    parser.add_argument(
        "--contexts", action="store_true", help="Print all contexts from a POT file"
    )
    parser.add_argument(
        "--incomplete",
        action="store_true",
        help="Print incomplete contexts from a PO file",
    )

    args = parser.parse_args()

    if args.contexts:
        print_contexts(args.file)
    elif args.incomplete:
        print_incomplete(args.file)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
