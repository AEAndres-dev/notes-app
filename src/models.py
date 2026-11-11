"""Note dataclass and serialization."""


class Note:
    """A single note."""

    def __init__(self, id, title, body, tags=None, created_at="", updated_at="",
                 schema_version=1, due_date=None):
        if tags is None:
            tags = []
        self.id = id
        self.title = title
        self.body = body
        self.tags = list(tags)
        self.created_at = created_at
        self.updated_at = updated_at
        self.schema_version = schema_version
        self.due_date = due_date
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
        if self.due_date is not None and not isinstance(self.due_date, str):
            raise ValueError("due_date must be a string or None")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "tags": list(self.tags),
            "schema_version": self.schema_version,
            "due_date": self.due_date,
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
        due_date = data.get("due_date")
        schema_version = data.get("schema_version", 1)
        return cls(
            id=note_id,
            title=title,
            body=body,
            tags=list(tags),
            created_at=created_at,
            updated_at=updated_at,
            schema_version=schema_version,
            due_date=due_date,
        )

    def __eq__(self, other):
        if not isinstance(other, Note):
            return False
        return self.to_dict() == other.to_dict()

    def __repr__(self):
        return "Note(%r)" % self.to_dict()
