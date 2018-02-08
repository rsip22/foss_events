Introduction
------------

The ExportPDF action enables the export of MoinMoin wiki pages as PDF
documents using XSLT, DocBook and XSL-FO external tools, or using either of
the htmldoc or wkhtmltopdf tools.

The use of XSL-FO and DocBook was indicated as a viable route to PDF output by
the existing RenderAsPDF action, but this action has been written
independently and has slightly different design criteria. For example, there
is no usage of JavaScript in the browser to indicate progress or to initiate
different processing steps. Furthermore, this action avoids creating files
explicitly and instead employs pipes where a multi-stage conversion occurs.

Installation
------------

The following configuration settings are present in the ExportPDF.py module:

PDF_EXPORT_MODE             Indicates the tool to use
                            ("docbook", "wkhtmltopdf", "htmldoc")

Depending on the above setting, the following settings may apply:

For "docbook":

  XSLT_PROCESSOR            Path to the xsltproc program
  FO_PROCESSOR              Path to the fop program
  DOCBOOK_STYLESHEET_BASE   Path to the directory containing DocBook resources

  Another setting that should not need modifying is the following:

  DOCBOOK_TO_FO_STYLESHEET  Relative path to the docbook.xsl stylesheet file
                            from the DOCBOOK_STYLESHEET_BASE path (putting
                            them together should reference the file with an
                            absolute path)

For "wkhtmltopdf":

  XVFB_WRAPPER              Path to the xvfb-run program
  WKHTMLTOPDF_PROCESSOR     Path to the wkhtmltopdf program

For "htmldoc":

  HTMLDOC_PROCESSOR         Path to the htmldoc program

Once configured, copy the ExportPDF.py module into your wiki's actions
directory.

With moinsetup and a suitable configuration file (see "Recommended Software"
below), you can perform this last step as follows, with $EPDIR referring to
the ExportPDF distribution directory:

  python moinsetup.py -f moinsetup.cfg -m install_actions $EPDIR/actions

Basic Usage
-----------

Select the ExportPDF action from the actions menu. After choosing a paper/page
size, a PDF document should be offered for download.

Choosing a Processor
--------------------

The mode used in the action, indicated using the PDF_EXPORT_MODE setting,
determines which processor or processing toolchain will be used to generate
PDF documents. Different processors have different advantages and
disadvantages and these are summarised below.

The "docbook" mode relies on Apache FOP which is a Java-based solution. This
obviously demands a functioning Java runtime environment, and the process of
setting up such an environment can be a chore. Moreover, the speed of the
resulting solution is not necessarily impressive, although the output is
better than the other processors.

The "wkhtmltopdf" mode relies on a virtual X server and a WebKit-based tool,
and the installation of such packages is likely to be much more convenient if
they are available in your operating system distribution. The output suffers
from being generated from wiki page HTML and problems with the wkhtmltopdf
tool itself such as clumsy pagination.

The "htmldoc" mode relies only on a single program, but this program does not
support UTF-8 content and also suffers from having to generate PDF output from
wiki page HTML.

In summary, the "docbook" mode is by far the recommended solution.

Improvement Suggestions
-----------------------

Some improvements could be made to this action:

  * Images need to be included in the output
  * More control over output options would be useful

Recommended Software
--------------------

See the "Dependencies" section below for essential software.

The moinsetup tool is recommended for installation since it aims to support
all versions of MoinMoin that are supported for use with this software.

See the following page for information on moinsetup:

http://moinmo.in/ScriptMarket/moinsetup

Dependencies
------------

The ExportPDF action has the following basic dependencies:

Packages                    Release Information
--------                    -------------------

MoinSupport                 Tested with 0.4.1
                            Source: http://hgweb.boddie.org.uk/MoinSupport

When used in the "docbook" mode, the following dependencies apply:

Packages                    Release Information
--------                    -------------------

xsltproc                    Tested with 1.1.26
                            Debian package: xsltproc
                            Source: http://www.xmlsoft.org/XSLT.html

Apache FOP                  Tested with 1.0
                            Debian package: fop
                            Source: http://xmlgraphics.apache.org/fop/

DocBook XSL                 Tested with 1.76.1
                            Debian package: docbook-xsl
                            Source: http://docbook.sourceforge.net/

Java                        Tested with a Java 6 runtime
                            Debian package: openjdk-6-jre-headless
                            Source: http://www.oracle.com/technetwork/java/index.html

The Java dependency is unfortunate and would ideally be avoided by using
something other than Apache FOP to convert XSL-FO content to PDF.

When used in the "wkhtmltopdf" mode, the following dependencies apply:

Packages                    Release Information
--------                    -------------------

wkhtmltopdf                 Tested with 0.9.9
                            Debian package: wkhtmltopdf
                            Source: https://code.google.com/p/wkhtmltopdf/

xvfb                        Tested with 1.12.4
                            Debian package: xvfb
                            Source: http://www.x.org/

When used in the "htmldoc" mode, the following dependencies apply:

Packages                    Release Information
--------                    -------------------

htmldoc                     Tested with 1.8.27
                            Debian package: htmldoc
                            Source: http://www.htmldoc.org/

Contact, Copyright and Licence Information
------------------------------------------

See the following Web page for more information about this work:

http://moinmo.in/ActionMarket/ExportPDF

The author of this packaging of the original work can be contacted at the
following e-mail address:

paul@boddie.org.uk

Copyright and licence information can be found in the docs directory - see
docs/COPYING.txt and docs/LICENCE.txt for more information.

Release Procedures
------------------

Update the actions/ExportPDF.py __version__ attribute.
Change the version number and package filename/directory in the documentation.
Update the release notes (see above).
Tag, export.
Archive, upload.
Update the ActionMarket and ActionMarket/ExportPDF page.
