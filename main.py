import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

RE_USER_ID = r"\bU[A-Z0-9]{7,12}\b"


def _get_users(p: Path) -> dict[str, str]:
    """
    Returns a dictionary mapping user ID to the user's name. If the user's name can't be determined, maps to the user
    ID.

    Args:
        p: The path to a users.json (or org_users.json) file

    Returns:
        A dictionary mapping user ID to name.
    """
    users = json.loads(p.read_text())
    return {u["id"]: u.get("real_name", u.get("name", u["id"])) for u in users}


def _translate_user_ids(msg: str, users: dict[str, str]) -> str:
    """
    Given a string and a dictionary mapping user ids to names, replaces all user IDs in the string with the
    corresponding name.

    Args:
        msg: The string to be updated
        users: A dictionary mapping user ID to user's name

    Returns:
        The input string with user IDs replaced by names
    """

    def _translate_user_id(m: re.Match) -> str:
        user_id: str = m.group(0)
        return users.get(user_id, user_id)

    return re.sub(
        RE_USER_ID,
        _translate_user_id,
        msg,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        type=Path,
        help="The directory to process",
    )
    args = parser.parse_args()
    d: Path = args.directory

    if not d.is_dir():
        print(f"{d.name} is not a directory")
        return

    csv_path = d / "output.csv"
    with csv_path.open("w") as fh:
        out = csv.DictWriter(fh, fieldnames=["timestamp", "user", "channel", "message"])
        out.writeheader()

        # Get a list of all users
        user_files = d.glob("**/*users.json")
        users = {}
        pbar = tqdm(user_files)
        pbar.set_description_str("Loading user files")
        for f in pbar:
            users = users | _get_users(f)

        # Get a list of all message files
        message_files = d.glob("**/????-??-??.json")
        pbar = tqdm(message_files)
        pbar.set_description_str("Loading message files")
        for mf in pbar:
            channel = mf.parent.name
            messages = json.loads(mf.read_text())
            for message in messages:
                user_id = message.get("user")
                user = users.get(user_id)
                out.writerow(
                    {
                        "timestamp": datetime.fromtimestamp(
                            float(message.get("ts"))
                        ).isoformat(),
                        "user": user,
                        "channel": channel,
                        "message": _translate_user_ids(message.get("text"), users),
                    }
                )
    print(f"Output written to {csv_path}")


if __name__ == "__main__":
    main()
