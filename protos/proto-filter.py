from util import get_haystack
import readline

ph = get_haystack()

results = []

def filter_by_tags(tags):
    for defn in ph.values():
        if all(tag in defn['tags'] for tag in tags):
            yield defn


def save():
    with open('output.csv', 'w') as f:
        for defn in results:
            f.write(defn + '\n')

while True:
    query = input('> ')
    if query == 'done':
        save()
        break
    else:
        results = results[:0]
        for ans in filter_by_tags(query.split(' ')):
            results.append(ans['proto'])
            print(ans['proto'])
