"""
Quick and dirty entity visualizer for documents in the database.
"""
import hug
import jinja2
from jinja2 import Environment, PackageLoader, select_autoescape

from visualizer.model import session, Document, Annotation

env = Environment(
    loader=PackageLoader('visualizer', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

suffix_output = hug.output_format.suffix({'.js': hug.output_format.json,
                                          '.html': hug.output_format.html})

_js_escapes = {
    '\\': '\\u005C',
    '\'': '\\u0027',
    '"': '\\u0022',
    '>': '\\u003E',
    '<': '\\u003C',
    '&': '\\u0026',
    '=': '\\u003D',
    '-': '\\u002D',
    ';': '\\u003B',
    u'\u2028': '\\u2028',
    u'\u2029': '\\u2029'
}
# Escape every ASCII character with a value less than 32.
_js_escapes.update(('%c' % z, '\\u%04X' % z) for z in range(32))


def jinja2_escapejs_filter(value):
    retval = []
    for letter in value:
        if letter in _js_escapes:
            retval.append(_js_escapes[letter])
        else:
            retval.append(letter)

    return jinja2.Markup("".join(retval))


env.filters['escapejs'] = jinja2_escapejs_filter
template = env.get_template('index.html')


@hug.get(examples='id=3499738', output=hug.output_format.html)
def documents(id: hug.types.number):
    """Render document text with its annotations."""
    doc = session.query(Document).filter_by(id=id).first()
    rows = session.query(Annotation).filter_by(document_id=id).all()
    spans = [{
        'start': row.start,
        'end': row.end + 1,
        'type': row.label.upper(),
    } for row in rows]
    print('got doc {}; {} spans'.format(id, len(spans)))
    index = template.render(
        text=doc.text,
        spans=spans,
        ents=['person', 'org', 'gpe', 'loc', 'product']
    )
    return index
