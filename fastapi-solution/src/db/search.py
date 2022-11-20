"""Search engine, the common interface"""


class Search:
    async def get_by_id(self, id_):
        raise NotImplementedError()

    async def search(self, query, from_, page_size,
                     sort_fields: list | None = None,
                     filter_items: list | None = None) -> list[dict]:
        raise NotImplementedError()
