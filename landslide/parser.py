# -*- coding: utf-8 -*-

import re

SUPPORTED_FORMATS = {
    'markdown': ['.mdown', '.markdown', '.markdn', '.md', '.mdn', '.mdwn'],
    'restructuredtext': ['.rst', '.rest'],
    'textile': ['.textile'],
}


class Parser(object):
    """This class generates the HTML code depending on which syntax is used in
       the souce document.

       The Parser currently supports both Markdown and restructuredText
       syntaxes.
    """
    RST_REPLACEMENTS = [
        (r'<div.*?>', r'', re.UNICODE),
        (r'</div>', r'', re.UNICODE),
        (r'<p class="system-message-\w+">.*?</p>', r'', re.UNICODE),
        (r'Document or section may not begin with a transition\.',
            r'', re.UNICODE),
        (r'<h(\d+?).*?>', r'<h\1>', re.DOTALL | re.UNICODE),
        (r'<hr.*?>\n', r'<hr />\n', re.DOTALL | re.UNICODE),
    ]

    md_extensions = ''

    def __init__(self, extension, encoding='utf8', md_extensions=''):
        """Configures this parser.
        """
        self.encoding = encoding
        self.format = None

        for supp_format, supp_extensions in SUPPORTED_FORMATS.items():
            for supp_extension in supp_extensions:
                if supp_extension == extension:
                    self.format = supp_format

        if not self.format:
            raise NotImplementedError(u"Unsupported format %s" % extension)

        if md_extensions:
            exts = (value.strip() for value in md_extensions.split(','))
            self.md_extensions = filter(None, exts)

    def _fix_list_spacing(self, text):
        """Insert blank lines before list markers that immediately follow non-list,
        non-blank content. Python's markdown library requires blank lines between
        paragraphs and lists; this preprocessing makes that unnecessary in source."""
        list_marker = re.compile(r'^[ \t]{0,3}(?:[-*+]|\d+\.)[ \t]')
        lines = text.split('\n')
        result = []
        in_fence = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```') or stripped.startswith('~~~'):
                in_fence = not in_fence
            if not in_fence and result and list_marker.match(line):
                prev = result[-1]
                if prev.strip() and not list_marker.match(prev):
                    result.append('')
            result.append(line)
        return '\n'.join(result)

    def parse(self, text):
        """Parses and renders a text as HTML regarding current format.
        """
        if self.format == 'markdown':
            try:
                import markdown
            except ImportError:
                raise RuntimeError(u"Looks like markdown is not installed")

            if text.startswith(u'\ufeff'):  # check for unicode BOM
                text = text[1:]

            text = self._fix_list_spacing(text)
            return markdown.markdown(text, extensions=self.md_extensions)
        elif self.format == 'restructuredtext':
            try:
                from landslide.rst import html_body
            except ImportError:
                raise RuntimeError(u"Looks like docutils are not installed")

            html = html_body(text, input_encoding=self.encoding)

            # RST generates pretty much markup to be removed in our case
            for (pattern, replacement, mode) in self.RST_REPLACEMENTS:
                html = re.sub(re.compile(pattern, mode), replacement, html, 0)

            return html.strip()
        elif self.format == 'textile':
            try:
                import textile
            except ImportError:
                raise RuntimeError(u"Looks like textile is not installed")

            text = text.replace('\n---\n', '\n<hr />\n')

            return textile.textile(text, html_type='html5')
        else:
            raise NotImplementedError(u"Unsupported format %s, cannot parse"
                                      % self.format)
