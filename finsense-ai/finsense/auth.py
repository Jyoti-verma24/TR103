import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timezone

import streamlit as st

from finsense.data import BASE_DIR

# ============================================================
# LOCAL ACCOUNTS
# ------------------------------------------------------------
# Accounts live in .data/users.json on this machine (git-ignored).
# Passwords are never stored: each one is salted and hashed with
# PBKDF2-HMAC-SHA256 (the standard library's slow password hash),
# and checked with a constant-time comparison.
# ============================================================

# FINSENSE_USERS_FILE lets tests point at a throwaway file, so they never touch real accounts.
USERS_PATH = os.environ.get("FINSENSE_USERS_FILE") or os.path.join(BASE_DIR, ".data", "users.json")
ITERATIONS = 240_000
MIN_PASSWORD = 8
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _load():
    try:
        with open(USERS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save(users):
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    tmp = USERS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
    os.replace(tmp, USERS_PATH)  # atomic, so a crash can't leave half a file


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONS).hex()


def _normalise(email):
    return (email or "").strip().lower()


def register(name, email, password, confirm):
    """Create an account. Returns (user, error)."""
    name, email = (name or "").strip(), _normalise(email)
    if not name:
        return None, "Please tell us your name."
    if not EMAIL_RE.match(email):
        return None, "That email address doesn't look right."
    if len(password or "") < MIN_PASSWORD:
        return None, f"Your password needs at least {MIN_PASSWORD} characters."
    if password != confirm:
        return None, "The two passwords don't match."

    users = _load()
    if email in users:
        return None, "There's already an account with this email. Try logging in instead."

    salt = secrets.token_hex(16)
    users[email] = {
        "name": name,
        "salt": salt,
        "hash": _hash(password, salt),
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _save(users)
    return {"email": email, "name": name}, None


def authenticate(email, password):
    """Check a login. Returns (user, error). Locks out briefly after repeated failures."""
    locked_until = st.session_state.get("auth_locked_until", 0)
    if time.time() < locked_until:
        return None, f"Too many attempts. Please wait {int(locked_until - time.time()) + 1} seconds."

    email = _normalise(email)
    record = _load().get(email)
    # Hash even when the email is unknown, so response time doesn't reveal which emails exist.
    salt = record["salt"] if record else "00" * 16
    ok = hmac.compare_digest(_hash(password or "", salt), record["hash"] if record else "")

    if not (record and ok):
        attempts = st.session_state.get("auth_attempts", 0) + 1
        st.session_state.auth_attempts = attempts
        if attempts >= MAX_ATTEMPTS:
            st.session_state.auth_locked_until = time.time() + LOCKOUT_SECONDS
            st.session_state.auth_attempts = 0
        return None, "That email and password don't match an account."

    st.session_state.auth_attempts = 0
    return {"email": email, "name": record["name"]}, None


def current_user():
    return st.session_state.get("user")


def sign_in(user):
    st.session_state.user = user


def sign_out():
    # Drop the user and everything they loaded, so the next person starts clean.
    for key in ["user", "finance_df", "data_source", "ingested_file", "dismissed"]:
        st.session_state.pop(key, None)
