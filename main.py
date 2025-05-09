import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path

RE_USER_ID = r"\bU[A-Z0-9]{7,12}\b"


def _get_users(p: Path) -> dict[str, str]:
    """
    Returns a dictionary mapping user ID to the user's name. If the user's name can't be determined, maps to the user ID.

    Args:
        p (Path): The path to a users.json (or org_users.json) file

    Returns:
        dict[str, str]: The dictionary mapping user ID to user's name.
    """
    users = json.loads(p.read_text())
    return {u["id"]: u.get("real_name", u.get("name", u["id"])) for u in users}


def _translate_users(msg: str, users: dict[str, str]) -> str:
    """
    Given a string and a user id to name map, replaces user IDs in the string with the user's name.

    Args:
        msg (str): The string to be updated
        users (dict[str, str]): A dictionary mapping user ID to user's name

    Returns:
        str: The input string with user IDs replaced by names
    """

    def _get_username_or_id(m: re.Match) -> str:
        user_id: str = m.group(0)
        return users.get(user_id, user_id)

    return re.sub(
        RE_USER_ID,
        _get_username_or_id,
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
    print(f"Writing output to {csv_path}")
    with csv_path.open("w") as fh:
        out = csv.DictWriter(fh, fieldnames=["timestamp", "user", "channel", "message"])
        out.writeheader()

        # Get a list of all users
        user_files = d.glob("**/*users.json")
        users = {}
        for f in user_files:
            users = users | _get_users(f)

        # Get a list of all message files
        message_files = d.glob("**/????-??-??.json")
        for mf in message_files:
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
                        "message": _translate_users(message.get("text"), users),
                    }
                )


if __name__ == "__main__":
    main()
