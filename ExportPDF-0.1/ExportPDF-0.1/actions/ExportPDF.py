# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Export as PDF action

    @copyright: 2013 by Paul Boddie <paul@boddie.org.uk>
    @license: GNU GPL (v2 or later), see COPYING.txt for details.
"""

from MoinMoin import caching
from MoinMoin.action import ActionBase, cache
from MoinMoin.wikiutil import escape
from MoinMoin.Page import Page
from MoinSupport import ActionSupport, escattr, getFormatterClass, formatText, get_send_headers
from os.path import join
import subprocess, os, codecs

__version__ = "0.1"

Dependencies = ['page']

# Configuration settings.

# Choose one value for the export mode.

PDF_EXPORT_MODE             = "docbook"
#PDF_EXPORT_MODE             = "wkhtmltopdf"
#PDF_EXPORT_MODE             = "htmldoc"

# Settings for "docbook" mode.

XSLT_PROCESSOR              = "/usr/bin/xsltproc"
FO_PROCESSOR                = "/usr/bin/fop"
DOCBOOK_STYLESHEET_BASE     = "/usr/share/xml/docbook/stylesheet"

# Tool settings for "docbook" mode.

DOCBOOK_TO_FO_STYLESHEET    = "docbook-xsl/fo/docbook.xsl"

# Settings for "wkhtmltopdf" mode.

XVFB_WRAPPER                = "/usr/bin/xvfb-run"
WKHTMLTOPDF_PROCESSOR       = "/usr/bin/wkhtmltopdf"

# Settings for "htmldoc" mode.

HTMLDOC_PROCESSOR           = "/usr/bin/htmldoc"

# NOTE: From docbook-xsl/fo/param.xsl.

docbook_paper_sizes = [
    "A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
    "B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10",
    "C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10",
    "A4landscape", "USletter", "USlandscape", "4A0", "2A0",
    ]

docbook_paper_size_labels = {
    "A4landscape" : "A4 landscape",
    "USletter" : "US letter",
    "USlandscape" : "US landscape",
    "4A0" : "Quadruple A0",
    "2A0" : "Double A0"
    }

wkhtmltopdf_paper_sizes = [
    "A4", "Letter"
    ]

wkhtmltopdf_paper_size_labels = {}

# NOTE: From the htmldoc man page.

htmldoc_paper_sizes = [
    "a4", "legal", "letter", "universal"
    ]

htmldoc_paper_size_labels = {
    "a4" : "A4",
    "legal" : "US legal",
    "letter" : "US letter",
    "universal" : "US universal"
    }

paper_sizes = {
    "docbook" : docbook_paper_sizes,
    "wkhtmltopdf" : wkhtmltopdf_paper_sizes,
    "htmldoc" : htmldoc_paper_sizes
    }

paper_size_labels = {
    "docbook" : docbook_paper_size_labels,
    "wkhtmltopdf" : wkhtmltopdf_paper_size_labels,
    "htmldoc" : htmldoc_paper_size_labels
    }

class ExportPDF(ActionBase, ActionSupport):

    "Export the current page as PDF."

    mode = PDF_EXPORT_MODE

    def _get_paper_sizes(self):
        return paper_sizes.get(self.mode)

    def _get_paper_size_labels(self):
        return paper_size_labels.get(self.mode)

    def get_form_html(self, buttons_html):

        "Return the action's form incorporating the 'buttons_html'."

        _ = self._
        request = self.request
        form = self.get_form()

        paper_size = form.get("paper-size", ["A4"])[0]

        paper_size_options = []
        paper_size_labels = self._get_paper_size_labels() or {}

        for size in self._get_paper_sizes() or []:
            paper_size_options.append('<option value="%s" %s>%s</option>' % (
                escattr(size), self._get_selected(size, paper_size),
                escape(_(paper_size_labels.get(size) or size))
                ))

        d = {
            "paper_size_label"      : escape(_("Paper size")),
            "paper_size_options"    : u"".join(paper_size_options),
            "buttons_html"          : buttons_html,
            "rev"                   : escattr(form.get("rev", ["0"])[0]),
            }

        return u"""\
<input name="rev" type="hidden" value="%(rev)s" />
<table>
    <tr>
        <td class="label"><label>%(paper_size_label)s</label></td>
        <td><select name="paper-size">%(paper_size_options)s</select></td>
    </tr>
    <tr>
        <td></td>
        <td class="buttons">%(buttons_html)s</td>
    </tr>
</table>
""" % d

    def do_action(self):

        "Attempt to post a comment."

        _ = self._
        form = self.get_form()
        request = self.request

        # Permit other revisions, but only if the current revision is readable.

        if not request.user.may.read(self.page.page_name):
            return 0, _("This page no longer allows read access.")

        self.page = Page(request, self.page.page_name, rev=int(form.get("rev", ["0"])[0]))

        # Check the paper size.

        paper_size = form.get("paper-size", [""])[0]

        if not paper_size in self._get_paper_sizes() or []:
            return 0, _("A paper size must be chosen.")

        # See if the revision is cached.

        cache_key = cache.key(request, content="%s-%s" % (self.page.get_real_rev(), paper_size))
        cache_entry = caching.CacheEntry(request, self.page, cache_key, scope="item")

        # Open any available cache entry and read it.

        if cache_entry.exists():
            cache_entry.open()
            try:
                self._write_pdf(cache_entry.read())
                return 1, None
            finally:
                cache_entry.close()

        # Otherwise, prepare the PDF.

        if self.mode == "docbook":
            return self._export_using_docbook(paper_size, cache_entry)
        elif self.mode == "wkhtmltopdf":
            return self._export_using_wkhtmltopdf(paper_size, cache_entry)
        elif self.mode == "htmldoc":
            return self._export_using_htmldoc(paper_size, cache_entry)
        else:
            return 0, _("The action must be configured to use a particular PDF generation tool.")

    def _get_page_as_html(self):

        "Get the page in HTML format."

        request = self.request
        page = self.page

        fmt = getFormatterClass(request, "text_html")(request)
        fmt.setPage(page)

        page_as_html = []
        append = page_as_html.append

        append("""\
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</head>
<body>
""")
        append(formatText(page.get_raw_body(), request, fmt, inhibit_p=False))
        append("""\
</body>
</html>
""")

        return u"".join(page_as_html)

    def _get_page_as_docbook(self):

        "Get the page in DocBook format."

        request = self.request
        page = self.page

        fmt = getFormatterClass(request, "text_docbook")(request)
        fmt.setPage(page)

        # The DocBook formatter needs to pretend a full document is being made.

        page_as_docbook = []
        append = page_as_docbook.append

        append(fmt.startDocument(page.page_name))
        append(fmt.startContent())
        append(formatText(page.get_raw_body(), request, fmt, inhibit_p=False).encode("utf-8"))
        append(fmt.endContent())
        append(fmt.endDocument())

        return "".join(page_as_docbook)

    def _write_pdf_for_html(self, p, page_as_html):

        """
        Write to the process 'p', the HTML for the page, reading the PDF output
        from the process and writing it to the browser.
        """

        writer = codecs.getwriter("utf-8")(p.stdin)
        writer.write(page_as_html)

        out, err = p.communicate()

        retcode = p.wait()

        if retcode != 0:
            return 0, err

        self._write_pdf(out)
        return 1, None

    def _export_using_wkhtmltopdf(self, paper_size, cache_entry):

        """
        Send the page HTML to the processor, indicating the given 'paper_size'.
        """

        p = subprocess.Popen([
            XVFB_WRAPPER, "--",
            WKHTMLTOPDF_PROCESSOR,
            "--page-size", paper_size,
            "-",
            "-"
            ],
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        return self._write_pdf_for_html(p, self._get_page_as_html(), cache_entry)

    def _export_using_htmldoc(self, paper_size, cache_entry):

        """
        Send the page HTML to the processor, indicating the given 'paper_size'.
        """

        os.environ["HTMLDOC_NOCGI"] = "1"

        p = subprocess.Popen([
            HTMLDOC_PROCESSOR,
            "-t", "pdf", "--quiet", "--webpage",
            "--size", paper_size,
            "-"
            ],
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        return self._write_pdf_for_html(p, self._get_page_as_html(), cache_entry)

    def _export_using_docbook(self, paper_size, cache_entry):

        """
        Send the page DocBook XML to the processor, indicating the given
        'paper_size'.
        """

        p1 = subprocess.Popen([
            XSLT_PROCESSOR,
            "-stringparam", "fop1.extensions", "1",
            "--stringparam", "paper.type", paper_size,
            join(DOCBOOK_STYLESHEET_BASE, DOCBOOK_TO_FO_STYLESHEET),
            "-"
            ],
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        p1.stdin.write(self._get_page_as_docbook())
        p1.stdin.close()

        # Pipe the XML-FO output to the FO processor.

        p2 = subprocess.Popen([
            FO_PROCESSOR,
            "-fo", "-",
            "-pdf", "-",
            ],
            shell=False,
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        out, err = p2.communicate()

        retcode = p1.wait()

        if retcode != 0:
            return 0, err

        retcode = p2.wait()

        if retcode != 0:
            return 0, err

        self._write_to_cache(out, cache_entry)
        self._write_pdf(out)
        return 1, None

    def _write_to_cache(self, out, cache_entry):

        "Write the output 'out' to the given 'cache_entry'."

        cache_entry.open(mode="w")
        try:
            try:
                cache_entry.write(out)
            finally:
                cache_entry.close()
        except IOError:
            if cache_entry.exists():
                cache_entry.remove()

    def _write_pdf(self, out):

        "Write the output 'out' to the request/response."

        request = self.request

        send_headers = get_send_headers(request)
        headers = ["Content-Type: application/pdf"]
        send_headers(headers)
        request.write(out)

    def render_success(self, msg, msgtype=None):

        """
        Render neither 'msg' nor 'msgtype' since a resource has already been
        produced.
        NOTE: msgtype is optional because MoinMoin 1.5.x does not support it.
        """

        pass

# Action invocation function.

def execute(pagename, request):
    ExportPDF(pagename, request).render()

# vim: tabstop=4 expandtab shiftwidth=4
