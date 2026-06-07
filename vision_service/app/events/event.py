class Event:

    def __init__(
        self,
        event_type,
        summary,
        metadata=None
    ):

        self.event_type = (
            event_type
        )

        self.summary = (
            summary
        )

        self.metadata = (
            metadata or {}
        )

    def __repr__(self):

        return (
            f"Event("
            f"type={self.event_type}, "
            f"summary={self.summary}"
            f")"
        )