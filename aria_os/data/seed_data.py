"""Seed default child, parent, and schedule on first run."""

from data import database as db


def seed():
    if not db.list_children():
        cid = db.create_child("Mazy", age=8, language="ar",
                              interests=["cars", "animals"],
                              triggers=["loud sounds"])
    else:
        cid = db.list_children()[0]["id"]

    db.get_or_create_default_parent()

    if not db.list_schedule(cid):
        for title, icon, time in [
            ("Brush teeth", "🪥", "08:00"),
            ("Breakfast",   "🍳", "08:15"),
            ("School",      "🎒", "08:45"),
            ("Rest",        "🛋️", "14:00"),
            ("Play",        "🧩", "16:00"),
            ("Bedtime",     "🌙", "20:30"),
        ]:
            db.add_schedule(cid, title, icon, time)


if __name__ == "__main__":
    seed()
