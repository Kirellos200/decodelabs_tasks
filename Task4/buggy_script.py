def process_data(data):
    # This is a comment
    result = []
    for item in data:
        if item.active:
            result.append(transform(item))
    return result