import logging
import pkg_resources
import requests

from urlparse import urlparse

from xblock.core import XBlock
from xblock.fields import Scope, Integer, String
from xblock.fragment import Fragment

log = logging.getLogger(__name__)


class EdxPc2JudgeBlock(XBlock):
    """
    An XBlock providing oEmbed capabilities for video (currently only supporting Vimeo)
    """

    problemname = String(help="URL of the video page at the provider", default=None, scope=Scope.content)
    problemnumber = Integer(help="Maximum width of the video", default=800, scope=Scope.content)
    allproblem = Integer(help="Maximum height of the video", default=450, scope=Scope.content)
    watched = Integer(help="How many times the student has watched it?", default=0, scope=Scope.user_state)

    def student_view(self, context):
        """
        Create a fragment used to display the XBlock to a student.
        `context` is a dictionary used to configure the display (unused)

        Returns a `Fragment` object specifying the HTML, CSS, and JavaScript
        to display.
        """
        provider, embed_code = self.get_embed_code_for_url(self.problemname)
        
        # Load the HTML fragment from within the package and fill in the template
        html_str = pkg_resources.resource_string(__name__, "static/html/simplevideo.html")
        frag = Fragment(unicode(html_str).format(self=self, embed_code=embed_code))

        # Load CSS
        css_str = pkg_resources.resource_string(__name__, "static/css/simplevideo.css")
        frag.add_css(unicode(css_str))

        # Load JS
        if provider == 'vimeo.com':
            js_str = pkg_resources.resource_string(__name__, "static/js/lib/froogaloop.min.js")
            frag.add_javascript(unicode(js_str))
            js_str = pkg_resources.resource_string(__name__, "static/js/src/simplevideo.js")
            frag.add_javascript(unicode(js_str))
            frag.initialize_js('SimpleVideoBlock')

        return frag

    def studio_view(self, context):
        """
        Create a fragment used to display the edit view in the Studio.
        """
        html_str = pkg_resources.resource_string(__name__, "static/html/simplevideo_edit.html")
        problemname = self.problemname or ''
        frag = Fragment(unicode(html_str).format(problemname=problemname, problemnumber=self.problemnumber, allproblem=self.allproblem))

        js_str = pkg_resources.resource_string(__name__, "static/js/src/simplevideo_edit.js")
        frag.add_javascript(unicode(js_str))
        frag.initialize_js('SimpleVideoEditBlock')

        return frag

    def get_embed_code_for_url(self, url):
        """
        Get the code to embed from the oEmbed provider
        """
        hostname = url and urlparse(url).hostname
        params = {
            'url': url,
            'format': 'json',
            'problemnumber': self.problemnumber,
            'allproblem': self.allproblem
        }

        # Check that the provider is supported
        if hostname == 'vimeo.com':
            oembed_url = 'http://vimeo.com/api/oembed.json'
            params['api'] = True
        else:
            return hostname, '<p>Unsupported video provider ({0})</p>'.format(hostname)
        
        try:
            r = requests.get(oembed_url, params=params)
            r.raise_for_status()
        except Exception as e:
            return hostname, '<p>Error getting video from provider ({error})</p>'.format(error=e)
        response = r.json()

        return hostname, response['html']

    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):
        """
        Called when submitting the form in Studio.
        """
        self.problemname = data.get('problemname')
        self.problemnumber = data.get('problemnumber')
        self.allproblem = data.get('allproblem')

        return {'result': 'success'}

    @XBlock.json_handler
    def mark_as_watched(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Called upon completion of the video
        """
        if not data.get('watched'):
            log.warn('not watched yet')
        else:
            self.watched += 1

        return {'watched': self.watched}

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("edxpc2judge", 
            """\
                <vertical_demo>
                    <edxpc2judge problemname="https://vimeo.com/46100581" problemnumber="800" />
                    <html_demo><div>Rate the video:</div></html_demo>
                    <thumbs />
                </vertical_demo>
             """)
        ]
