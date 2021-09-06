from utils.header_parse import DecoratedHeader, MultiValueHeader, Header


def guess(acceptable, provided, default):
    #if len(provided) == 0:
    #    if type(body) == bytes:
    #        write_type(body, "application/octet-stream")
    #        return

    if not isinstance(acceptable, Header) and len(acceptable) == len(provided) == 0:
        return default

    found = {}

    for content_type in provided:
        if isinstance(acceptable, Header):
            if acceptable == content_type:
                return content_type
            else:
                continue

        if content_type in acceptable:
            ct = acceptable[content_type] if isinstance(acceptable, MultiValueHeader) else acceptable
            if isinstance(ct, DecoratedHeader):
                try:
                    found[ct.value] = float(ct["q"])
                except ValueError:
                    return default
            else:
                found[ct.value] = 0.0

    if len(found) == 0:
        return default

    k = max(found, key=found.get)

    if k is None:
        return default

    return k
