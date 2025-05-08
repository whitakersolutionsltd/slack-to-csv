import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path

RE_CHANNEL_DUMP_FILENAME = r"\d{4}-\d{2}-\d{2}.json"
RE_USER_ID = r"\bU[A-Z0-9]{7,12}\b"


def _get_users(p: Path) -> dict[str, str]:
    # Just return the raw user dictionaries
    users = json.loads(p.read_text())
    return {u["id"]: u.get("real_name", u.get("name", "Anonymous User")) for u in users}


def _translate_users(msg: str, users: dict[str, str]) -> str:
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
    with csv_path.open("w") as fh:
        out = csv.DictWriter(fh, fieldnames=["time", "user", "channel", "message"])
        out.writeheader()

        # Get a list of all users
        user_files = d.glob("**/*users.json")
        users = {}
        for f in user_files:
            users = users | _get_users(f)

        # Get the messages
        message_files = d.glob("**/????-??-??.json")
        for mf in message_files:
            channel = mf.parent.name
            messages = json.loads(mf.read_text())
            for message in messages:
                user_id = message.get("user")
                user = users.get(user_id)
                out.writerow(
                    {
                        "time": datetime.fromtimestamp(
                            float(message.get("ts"))
                        ).isoformat(),
                        "user": user,
                        "channel": channel,
                        "message": _translate_users(message.get("text"), users),
                    }
                )


if __name__ == "__main__":
    main()
