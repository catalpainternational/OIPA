from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import urllib.request, urllib.error, urllib.parse
import http.client
import logging
import http.cookiejar

logger = logging.getLogger(__name__)

class FileGrabber(object):

    def get_the_file(self, url, try_number = 0):
        import mechanize
        try:

            br = mechanize.Browser()

            # Cookie Jar
            cj = http.cookiejar.LWPCookieJar()
            br.set_cookiejar(cj)

            # Browser options
            br.set_handle_equiv(True)
            br.set_handle_redirect(True)
            br.set_handle_referer(True)
            br.set_handle_robots(False)
            br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
            br.set_debug_http(True)
            br.set_debug_redirects(True)
            br.set_debug_responses(True)

            # User-Agent
            br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

            response = br.open(url, timeout=80)
            return response

        except urllib.error.HTTPError as e:
            logger.info('HTTPError (url=' + url + ') = ' + str(e.code))
            if try_number < 6:
                self.get_the_file(url, try_number + 1)
            else:
                return None
        except urllib.error.URLError as e:
            logger.info('URLError (url=' + url + ') = ' + str(e.reason))
            if try_number < 6:
                self.get_the_file(url, try_number + 1)
        except http.client.HTTPException as e:
            logger.info('HTTPException reading url ' + url)
            if try_number < 6:
                self.get_the_file(url, try_number + 1)
        except Exception as e:
            logger.info('%s (%s)' % (e.message, type(e)) + " in get_the_file: " + url)
            if try_number < 6:
                self.get_the_file(url, try_number + 1)
