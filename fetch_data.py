"""Download the gait recordings and ingest them into SQLite.

    python fetch_data.py                      # the six default subjects
    python fetch_data.py --subjects GaPt05,SiCo02
    python fetch_data.py --list               # what the dataset offers
    python fetch_data.py --force              # re-download even if present

Data comes from the PhysioNet *Gait in Parkinson's Disease* database
(gaitpdb v1.0.0), released under the Open Data Commons Attribution License v1.0.
"""

import argparse
import sys

import gaitdata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    parser.add_argument(
        "--subjects",
        help="comma-separated subject ids, e.g. GaPt03,JuCo01 "
        f"(default: {','.join(gaitdata.DEFAULT_SUBJECTS)})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list every subject in the dataset and exit",
    )
    parser.add_argument(
        "--force", action="store_true", help="re-download files already on disk"
    )
    args = parser.parse_args(argv)

    if args.list:
        gaitdata.download(subject_ids=[], log=lambda _: None)
        demographics = gaitdata.read_demographics()
        print(f"{'ID':<10} {'STUDY':<6} {'GROUP':<12} {'AGE':>4}")
        for _, row in demographics.iterrows():
            group = gaitdata.GROUP_LABELS.get(int(row["Group"]), "?")
            age = row["Age"]
            print(f"{row['ID']:<10} {row['Study']:<6} {group:<12} {age:>4.0f}")
        print(f"\n{len(demographics)} subjects.")
        return 0

    subjects = args.subjects.split(",") if args.subjects else None

    print(f"Downloading from {gaitdata.BASE_URL}")
    gaitdata.download(subject_ids=subjects, force=args.force)

    print("\nIngesting into", gaitdata.DB_PATH)
    ingested = gaitdata.ingest(subject_ids=subjects)

    print(f"\nReady: {len(ingested)} subjects. Start the dashboard with `python app.py`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
