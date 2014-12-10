import logging
import pkg_resources
import requests
import cgi
import socket
import sys
from urlparse import urlparse
from xblock.core import XBlock
from xblock.fields import Boolean, DateTime, Scope, String, Float, Integer,ScopeIds
from xblock.fragment import Fragment
log = logging.getLogger(__name__)


class EdxPc2JudgeBlock(XBlock):
    """
    An XBlock providing oEmbed capabilities for video (currently only supporting Vimeo)
    """
    edxid = String(help="URL of the video page at the provider", default=None, scope=Scope.user_state)
    problemname = String(help="URL of the video page at the provider", default=None, scope=Scope.content)
    problemnumber = Integer(help="Maximum width of the video", default=1, scope=Scope.content)
    allproblem = Integer(help="Maximum height of the video", default=450, scope=Scope.content)
    warnning = Integer(help="How many times the student has watched it?", default=0, scope=Scope.user_state)

    def student_view(self, context):
        HOST, PORT = "140.115.51.227", 9876
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.problemtext=3
        studentid =str(self.xmodule_runtime.anonymous_student_id)
        self.edxid = studentid
        sock.connect((HOST, PORT))
        sock.sendall(studentid)
        sock.close()
        HOST2, PORT2 = "140.115.51.227", 9888
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock2.connect((HOST2, PORT2))
        sock2.sendall(studentid)
        ok = sock2.recv(1024).strip()
        sock2.sendall(str(self.problemnumber))
        choose = sock2.recv(1024).strip()
        sock2.close()
        html_str = pkg_resources.resource_string(__name__, "static/html/Pc2Judge.html")
        frag = Fragment(unicode(html_str).format(edxid=self.edxid,problemnumber=self.problemnumber))
        if(choose=="None"):
            self.edxid = studentid
            js_str = pkg_resources.resource_string(__name__, "static/js/src//Pc2Judge_1.js")
            frag.add_javascript(unicode(js_str))
            frag.initialize_js('Pc2JudgeBlock')
        elif(choose=="YES"):
            self.edxid = studentid
            js_str = pkg_resources.resource_string(__name__, "static/js/src//Pc2Judge_2.js")
            frag.add_javascript(unicode(js_str))
            frag.initialize_js('Pc2JudgeBlock2')
        elif(choose=="NO"):
            self.edxid = studentid
            js_str = pkg_resources.resource_string(__name__, "static/js/src//Pc2Judge_3.js")
            frag.add_javascript(unicode(js_str))
            frag.initialize_js('Pc2JudgeBlock3')
        #html_str = pkg_resources.resource_string(__name__, "static/html/Pc2Judge2.html")
        #sock.connect((HOST, PORT))
        #sock.sendall(test)
        #sock.sendall(test)
        #sock.close()
        #frag.initialize_js('Pc2JudgeBlock')
        return frag

    def studio_view(self, context):
        """
        Create a fragment used to display the edit view in the Studio.
        """
        html_str = pkg_resources.resource_string(__name__, "static/html/Pc2Judge_edit.html")
        problemname = self.problemname or ''
        frag = Fragment(unicode(html_str).format(problemname=problemname, problemnumber=self.problemnumber, allproblem=self.allproblem))

        js_str = pkg_resources.resource_string(__name__, "static/js/src/Pc2Judge_edit.js")
        frag.add_javascript(unicode(js_str))
        frag.initialize_js('Pc2JudgeEditBlock')

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
        """
        HOST, PORT = "140.115.51.227", 9889
        sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock3.connect((HOST, PORT))
        sock3.sendall(str(self.problemnumber))
        check = sock.recv(1024).strip()
        if(check=='warn'):
            self.warnning=1
        sock.close()
        """
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
