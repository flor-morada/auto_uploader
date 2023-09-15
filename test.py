def concat_elements(slist, startpos, stoppos):
    if startpos > stoppos:
        slist = []
    if stoppos >= len(slist):
        stoppos = len(slist) - 1
    if startpos < 0:
        startpos = 0

    new_string = ""
    while startpos <= stoppos:
        new_string += str(slist[startpos])
        startpos += 1

    return new_string


def get_evens(lst):
    return [x for x in lst if x % 2 == 0]
