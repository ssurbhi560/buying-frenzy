from flask import current_app


def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, body=payload)


def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index, field, query):
    if not current_app.elasticsearch:
        return []

    search = current_app.elasticsearch.search(
        index=index,
        body={"query": {"match": {field: {"query": query, "fuzziness": "AUTO"}}}},
    )
    return [int(hit["_id"]) for hit in search["hits"]["hits"]]
