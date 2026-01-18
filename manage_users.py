import argparse
import json
import os
from getpass import getpass

from auth import hash_password


def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {"users": {}}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        data = {}
    data.setdefault("users", {})
    if not isinstance(data["users"], dict):
        data["users"] = {}
    return data


def _save(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def cmd_add(args: argparse.Namespace) -> int:
    data = _load(args.file)
    username = args.username

    pw1 = getpass("Password: ")
    pw2 = getpass("Confirm: ")
    if pw1 != pw2:
        raise SystemExit("Passwords do not match")

    data["users"][username] = {
        "password": hash_password(pw1),
        "permissions": args.permissions,
    }

    _save(args.file, data)
    print(f"Saved user '{username}' to {args.file}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    data = _load(args.file)
    if args.username in data.get("users", {}):
        del data["users"][args.username]
        _save(args.file, data)
        print(f"Removed user '{args.username}'")
        return 0
    print(f"User '{args.username}' not found")
    return 1


def cmd_list(args: argparse.Namespace) -> int:
    data = _load(args.file)
    users = data.get("users", {})
    if not users:
        print("No users")
        return 0
    for username, record in users.items():
        perms = record.get("permissions", []) if isinstance(record, dict) else []
        print(f"- {username}: {perms}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Manage Streamlit app users")
    p.add_argument("--file", default="users.json", help="Path to users.json")

    sub = p.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="Add or update a user")
    add.add_argument("--username", required=True)
    add.add_argument(
        "--permissions",
        nargs="+",
        choices=["encode", "decode"],
        required=True,
        help="Permissions for this user",
    )
    add.set_defaults(func=cmd_add)

    rm = sub.add_parser("remove", help="Remove a user")
    rm.add_argument("--username", required=True)
    rm.set_defaults(func=cmd_remove)

    ls = sub.add_parser("list", help="List users")
    ls.set_defaults(func=cmd_list)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
