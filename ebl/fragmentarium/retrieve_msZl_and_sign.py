from ebl.app import create_context

if __name__ == "__main__":
    context = create_context()
    signs = context.sign_repository.find_many({})
    no_unicode = []
    for sign in signs:
        name = sign.name
        mzl = next(filter(lambda record: record.name == "MZL", sign.lists), None)
        if not len(sign.unicode):
            no_unicode.append(sign)
        else:
            unicode = sign.unicode[0]
            print(f"{sign.name} {chr(unicode)}")
    for counter, sign in enumerate(no_unicode):
        print(f"{sign.name} {chr(counter+ 200)}")
        
