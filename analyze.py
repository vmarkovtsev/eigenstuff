from __future__ import print_function

import bs4, itertools, matplotlib, numpy, os, random, re, requests, sys, time
from matplotlib import pyplot

cache = {}
if os.path.exists('cache.tsv'):
    for line in open('cache.tsv'):
        q, n = line.strip().split('\t')
        cache[q] = int(n)

def get_n_results_dumb(q):
    r = requests.get('http://www.google.com/search',
                     params={'q': q,
                             "tbs": "li:1"})
    r.raise_for_status()
    soup = bs4.BeautifulSoup(r.text)
    s = soup.find('div', {'id': 'resultStats'}).text
    if not s:
        return 0
    m = re.search(r'([0-9,]+)', s)
    return int(m.groups()[0].replace(',', ''))

def page_rank(m, beta=0.85, niter=20):
    N = m.shape[0]
    x = numpy.ones(N, dtype=numpy.float32) / N
    for i in range(niter):
        x_next = m.dot(x) * beta
        x_next += (1 - beta) / N  # ***
        xdiff = numpy.linalg.norm(x - x_next, ord=1)
        x = x_next
        print(("iter #%d: %f" % (i + 1, xdiff)))
    return x

if True:
    tag = 'prog_lang'
    items = ['java', 'c', 'c++', 'c#', 'python', 'visual basic', 'node', 'perl', 'php', 'ruby', 'go', 'swift', 'dart', 'objective c', 'cobol', 'fortran', 'lua', 'scala', 'lisp', 'haskell', 'rust', 'erlang', 'clojure', 'matlab', 'pascal', 'r', 'elixir', 'kotlin'] #, 'prolog', 'typescript']
    verbs_ij = ['switch', 'switched', 'move', 'moved', 'code']
elif False:
    tag = 'js_framework'
    items = ['react', 'angular', 'vue', 'backbone', 'ember', 'knockout', 'jquery']
    verbs_ij = ['switch', 'switched', 'move', 'moved']
elif False:
    tag = 'database'
    items = ['mysql', 'postgres', 'mongodb', 'cassandra', 'dynamodb', 'mariadb']
    verbs_ij = ['switch', 'switched', 'move', 'moved']
else:
    tag = 'taxi_app'
    items = ['uber', 'lyft', 'gett', 'juno', 'curb', 'via', 'summon', 'bridj', 'way2ride', 'arro', 'flywheel', 'sidecar', 'hailo', 'ola', 'grab', 'easy taxi', 'didi dache', 'lecab', 'cabify', 'careem']
    verbs_ij = ['switch', 'switched', 'move', 'moved']

item2i = dict([(item, i) for i, item in enumerate(items)])

qs = []
for item1, item2 in itertools.product(items, items):
    if item1 != item2:
        for verb in verbs_ij:
            qs.append((item2i[item1], item2i[item2], '"%s from %s to %s"' % (verb, item1, item2)))
            qs.append((item2i[item1], item2i[item2], '"%s to %s from %s"' % (verb, item2, item1)))

m = numpy.zeros((len(items), len(items)))
random.shuffle(qs)
print(100. * len(set(cache).intersection([q for _, _, q in qs])) / len(qs))

for i, j, q in qs:
    if q in cache:
        n = cache[q]
    else:
        sys.stdout.write('%50s...' % q)
        sys.stdout.flush()
        n = get_n_results_dumb(q)
        sys.stdout.write('%9d\n' % n)
        f = open('cache.tsv', 'a')
        f.write('%s\t%d\n' % (q, n))
        f.close()
    m[j][i] += n

def plot_mat(m, items, cm, fn, text=False, dir_text=None):
    s = 4 + len(items) * 0.3
    fig = pyplot.figure(figsize=(s, s))
    ax = fig.add_subplot(111)
    ax.xaxis.set_label_position('top')
    ax.matshow(m.T + 1, cmap=cm, norm=matplotlib.colors.LogNorm(vmin=numpy.min(m+1), vmax=numpy.max(m+1)))

    if dir_text:
        ax.set_xlabel('To language\n< Smaller %s %10s Larger %s >' % (dir_text, '', dir_text))
        ax.set_ylabel('From language\n< Larger %s %10s Smaller %s >' % (dir_text, '', dir_text))
    else:
        ax.set_xlabel('To language')
        ax.set_ylabel('From language')
    ax.set_xticks(numpy.arange(0, len(items)))
    ax.set_yticks(numpy.arange(0, len(items)))
    ax.set_xticklabels(items, rotation=90, ha='center')
    ax.set_yticklabels(items, va='center')
    ax.set_xticks(numpy.arange(0.5, len(items)+0.5), minor=True)
    ax.set_yticks(numpy.arange(0.5, len(items)+0.5), minor=True)
    ax.grid(which='minor')

    if text:
        for i in range(len(items)):
            for j in range(len(items)):
                ax.text(i, j, str(int(m[i][j])), va='center', ha='center', size=7)

    fig.tight_layout()
    pyplot.savefig(fn, dpi=300)

# Plot lexicographical
ps = sorted(list(range(len(items))), key=lambda i: items[i])
plot_mat(m[ps,:][:,ps], sorted(items), pyplot.cm.OrRd, '%s_matrix.png' % tag, text=True)

m += numpy.eye(len(items)) # hack to fix zero entries
for item, pop in zip(items, m.sum(axis=0) + m.sum(axis=1)):
    print(('%20s %6d' % (item, pop)))
m /= m.sum(axis=0)[numpy.newaxis,:]
u = numpy.ones(len(items))

for i in range(100):
    u = numpy.dot(m, u)
    u /= u.sum()

# Create a new matrix where rows/columns are ordered by u
ps = sorted(list(range(len(items))), key=lambda i: u[i])
for p in reversed(ps):
    print(('| %5.2f%% | %20s |' % (u[p]*100, items[p])))

m_new = m[ps,:][:,ps]

prs = page_rank(m_new)
for pr, lang in sorted(zip(prs, [items[p] for p in ps]), reverse=True):
    print("%12s\t%.3f" % (lang, pr))

plot_mat(m_new, [items[p] for p in ps], pyplot.cm.BuGn, '%s_matrix_eig.png' % tag, dir_text='future popularity')
