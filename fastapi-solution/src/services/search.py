"""Search engine, the common interface"""
class Search:
    async def get_by_id(self, id_):
        raise NotImplementedError()

    async def search(self, query, from_, page_size) -> list[dict]:
        raise NotImplementedError()