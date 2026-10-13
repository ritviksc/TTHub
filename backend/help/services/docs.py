"""Load the help articles in help/content/. They feed both the Help page and the RAG index.

Articles live in one folder per audience, and the folder decides who may read
them: Super Admins read everything, Branch Managers also read the Kaimahi docs
(so they can support their kaimahi), and everyone reads `general/`.
"""
import re
from dataclasses import dataclass
from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
ROLES = ("super_admin", "branch_manager", "instructor")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

# Folder -> (label shown in the explorer and to the LLM, roles that may read it).
# Dict order is the order the folders appear in on the Help page.
AUDIENCES = {
    "general": ("General", ROLES),
    "kaimahi": ("Kaimahi", ROLES),
    "branch-manager": ("Branch Manager", ("super_admin", "branch_manager")),
    "super-admin": ("Super Admin", ("super_admin",)),
}


@dataclass(frozen=True)
class Doc:
    slug: str
    title: str
    section: str
    order: int
    audience: str
    body: str

    @property
    def audience_label(self):
        return AUDIENCES[self.audience][0]

    @property
    def roles(self):
        return AUDIENCES[self.audience][1]


def audiences_for(role):
    return [audience for audience, (_, readers) in AUDIENCES.items() if role in readers]


def parse_front_matter(text, source="article"):
    """Split `---` front-matter from the body.

    Only the keys we use are supported (title, section, order), so a YAML
    library is not needed. A malformed article fails loudly.
    """
    text = text.lstrip("﻿")
    match = re.match(r"---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    if not match:
        raise ValueError(f"{source}: missing front-matter")
    meta = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"{source}: bad front-matter line {line!r}")
        meta[key.strip()] = value.strip().strip("\"'")

    unknown = set(meta) - {"title", "section", "order"}
    if unknown:
        raise ValueError(f"{source}: unknown front-matter keys {', '.join(sorted(unknown))}")
    for key in ("title", "section"):
        if not meta.get(key):
            raise ValueError(f"{source}: {key} is required")
    try:
        order = int(meta.get("order", 100))
    except ValueError:
        raise ValueError(f"{source}: order must be a whole number") from None
    return {"title": meta["title"], "section": meta["section"], "order": order}, text[match.end():].strip()


def load_docs(content_dir=CONTENT_DIR):
    """Every article, in explorer order: audience folder, then order, then title.

    The file name is the slug and must be unique across all folders, because
    links and chatbot citations use the slug alone.
    """
    content_dir = Path(content_dir)
    stray = [path.name for path in content_dir.glob("*.md")]
    if stray:
        raise ValueError(f"{', '.join(stray)}: articles must be inside an audience folder")
    docs, seen = [], {}
    for folder in sorted(path for path in content_dir.iterdir() if path.is_dir()):
        if folder.name not in AUDIENCES:
            raise ValueError(f"{folder.name}/: unknown audience folder (use {', '.join(AUDIENCES)})")
        for path in sorted(folder.glob("*.md")):
            slug = path.stem
            if not SLUG.fullmatch(slug):
                raise ValueError(f"{folder.name}/{path.name}: file names must be lower-case-with-hyphens")
            if slug in seen:
                raise ValueError(f"{folder.name}/{path.name}: slug already used by {seen[slug]}/{path.name}")
            seen[slug] = folder.name
            meta, body = parse_front_matter(path.read_text(encoding="utf-8"), f"{folder.name}/{path.name}")
            docs.append(Doc(slug=slug, audience=folder.name, body=body, **meta))
    position = list(AUDIENCES)
    return sorted(docs, key=lambda doc: (position.index(doc.audience), doc.order, doc.title.lower()))


def docs_for(role, content_dir=CONTENT_DIR):
    return [doc for doc in load_docs(content_dir) if role in doc.roles]


def get_doc(role, slug, content_dir=CONTENT_DIR):
    """The article, or None when it does not exist or this role may not read it."""
    return next((doc for doc in docs_for(role, content_dir) if doc.slug == slug), None)
