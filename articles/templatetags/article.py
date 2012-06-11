from django import template
from articles.models import Article

register = template.Library()


def parse_tokens(parser, bits):
    """
    Parse a tag bits (split tokens) and return a list on kwargs (from bits of the  fu=bar) and a list of arguments.
    """

    kwargs = {}
    args = []
    for bit in bits[1:]:
        try:
            try:
                pair = bit.split('=')
                kwargs[str(pair[0])] = parser.compile_filter(pair[1])
            except IndexError:
                args.append(parser.compile_filter(bit))
        except TypeError:
            raise template.TemplateSyntaxError('Bad argument "%s" for tag "%s"' % (bit, bits[0]))

    return args, kwargs


class ArticlesNode(template.Node):
    """
        Output a list of articles.
        If as varname is specified then add the result to the context.

        Usage:
            {% articles %}
            OR
            {% articles articles %}
            OR
            {% articles articles limit %}
            OR
            {% articles as artilce_list %}
            OR
            {% articles articles as artilce_list %}
            OR
            {% articles limit=limit as artilce_list %}
    """
    def __init__(self, articles=None, limit=None, varname=None):
        self.articles = articles
        self.limit = limit
        self.varname = varname

    def render(self, context):
        articles = self.articles and self.articles.resolve(context)
        limit = self.limit and self.limit.resolve(context)


        if articles is None:
            user = None
            if 'request' in context:
                user = context['request'].user
            articles = Article.objects.active(user=user).select_related()

        if limit is not None:
            articles = articles[:limit]


        if self.varname is not None:
            context[self.varname] = articles
            return ''
        else:
            t = template.loader.select_template(['articles/articles.html'])
            context.push()
            context['articles'] = articles
            output = t.render(context)
            context.pop()

            return output


@register.tag()
def articles(parser, token):
    bits = token.split_contents() 

    varname = None
    try:
        if bits[-2] == 'as':
            varname = bits[-1]
            bits = bits[:-2]
    except IndexError:
        pass

    args, kwargs = parse_tokens(parser, bits)
    if varname is not None:
        kwargs['varname'] = varname

    return ArticlesNode(*args, **kwargs)

