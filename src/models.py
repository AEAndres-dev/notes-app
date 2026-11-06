"""Note dataclass and serialization."""


class Note:
    """A single note."""

    def __init__(self, id, title, body, tags=None, created_at="", updated_at=""):
        if tags is None:
            tags = []
        self.id = id
        self.title = title
        self.body = body
        self.tags = list(tags)
        self.created_at = created_at
        self.updated_at = updated_at
        self._validate()

    def _validate(self):
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("id must be a non-empty string")
        if not isinstance(self.title, str):
            raise ValueError("title must be a string")
        if not isinstance(self.body, str):
            raise ValueError("body must be a string")
        if not isinstance(self.tags, list) or not all(isinstance(t, str) for t in self.tags):
            raise ValueError("tags must be a list of strings")
        if not isinstance(self.created_at, str):
            raise ValueError("created_at must be a string")
        if not isinstance(self.updated_at, str):
            raise ValueError("updated_at must be a string")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "tags": list(self.tags),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("note must be a JSON object")
        note_id = data.get("id")
        if not isinstance(note_id, str) or not note_id:
            raise ValueError("id must be a non-empty string")
        title = data.get("title")
        if not isinstance(title, str):
            raise ValueError("title must be a string")
        body = data.get("body")
        if not isinstance(body, str):
            raise ValueError("body must be a string")
        tags = data.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            raise ValueError("tags must be a list of strings")
        created_at = data.get("created_at", "")
        if not isinstance(created_at, str):
            raise ValueError("created_at must be a string")
        updated_at = data.get("updated_at", "")
        if not isinstance(updated_at, str):
            raise ValueError("updated_at must be a string")
        return cls(
            id=note_id,
            title=title,
            body=body,
            tags=list(tags),
            created_at=created_at,
            updated_at=updated_at,
        )

    def __eq__(self, other):
        if not isinstance(other, Note):
            return False
        return self.to_dict() == other.to_dict()

    def __repr__(self):
        return "Note(%r)" % self.to_dict()
