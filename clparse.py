import re
import urllib
import urllib2
from datetime import date
from BeautifulSoup import BeautifulSoup

class Listing:

    def __init__(self, text):
        self.text = text
        self.loc = self.parse_loc(text)
        self.owner = self.parse_owner(text)
        self.price = self.parse_price(text)
        self.url = self.parse_url(text)
        self.googleMapLink = self.parse_google_map_url(text)

    def __str__(self):
        output = "" + self.loc + "--" + self.price + "--"
        if self.owner:
            output += "owner"
        else:
            output += "agent"
        return output

    def parse_loc(self, text):
        if text.font:
            return text.font.renderContents()
        else:
            return "No location"

    def parse_owner(self, text):
        if text.small:
            return re.search("apts by owner", text.small.renderContents()) != None
        else:
            return False

    def parse_price(self, text):
        listing_desc = text.find('a').renderContents()
        price = listing_desc[1:5]
        return price
    
    def parse_url(self, text):
        """parse out CL page url from link"""
        anchor = text.find('a')
        if anchor:
            return anchor['href']
        else:
            return ""
    
    def parse_google_map_url(self, text):
        """go to the url for the listing, and get a google maps link to it's location, if one exists"""
        listing_url = self.url if self.url else self.parse_url(text)
        listing_page = BeautifulSoup(urllib2.urlopen(listing_url).read())
        #first, try to find a google maps link already formed
        linksToGoogleMaps = listing_page.findAll('a', href=re.compile('maps.google.com'))
        for tag in linksToGoogleMaps:
            if tag.find(text=re.compile("google map")):
                return tag['href']
        #if this didn't work, try to find a location
        #then construct a google maps link from it
        geoAreaCLTAG =  listing_page.find(text=re.compile("CLTAG GeographicArea"))
        if geoAreaCLTAG is None:
            return ''
        location = geoAreaCLTAG[geoAreaCLTAG.index('=')+1:].strip()\
        #need to have '+' instead of spaces
        locationWithPluses = '+'.join(location.split())
        googleMapsLink = 'https://maps.google.com/?q=loc%3A+' + locationWithPluses
        return googleMapsLink
                                    
    def print_link(self):
        """print html formatted link to Listing page"""
        link = ""
        link += '<a href="' + self.url + '">' + str(self) + "</a>" + '\t<a href="' + self.googleMapLink + '"> google map</a>'
        if self.owner:
            link = "<b>" + link + "</b>"
        
        return link


#Utilities for groups of Listings
def sift_by_location(listings, terms):
    """Pare list of items by match locations with terms"""
    results = []
    for listing in listings:
        for term in terms:
            if re.search(term, listing.loc, re.I):
                results.append(listing)
                break

    return results

def parse_page(page, today):
    """Create list of listing items from CL page
    
         return list of items and boolean representing whether to continue search"""
    print page.title
    lines = page.findAll('p')
    items = []
    for line in lines:
        if re.search(today, line.renderContents()):
            items.append(Listing(line))
        else:
            return (items, True)

    return (items, False)

def dedupe(listings):
    """remove listings with identical titles"""
    results = [] 
    for idx, val in enumerate(listings):
        original = True
        for comp in listings[idx+1:]:
            if (comp.text.find('a').renderContents() == 
                    val.text.find('a').renderContents() or
                 comp.url == val.url):
                original = False
                break
        if original:
            results += [val]

    return results

def compile_listings(url, **params):
    """Create list of listing items from search terms"""
    listings = []
    params['s'] = 0 #paging counter
    today = date.today().strftime("%b ") + str(date.today().day)
    finished = False
    while not finished:
        bs_page = open_page(url, params)
        tmp_listings, finished = parse_page(bs_page, today)
        listings += tmp_listings
        params['s'] += 100
        if params['s'] >= 1000:
            finished = True

    listings = dedupe(listings)
    return listings

def open_page(url, search_params):
    """create beautifulsoup object from url"""
    url_params = urllib.urlencode(search_params)
    login_fobj = urllib2.urlopen(url + "?" + url_params) 
    return BeautifulSoup(login_fobj.read()) 

if __name__ == '__main__':    
    listings = compile_listings("http://boston.craigslist.org/search/aap", 
                            bedrooms = '5', 
                            query = 'somerville|davis|porter|ball|tufts')

    listings.sort(key=lambda listing: listing.price)
    listings = sift_by_location(listings, ["somerville", "porter", "davis", 
                                              "ball", "tufts", "cambridge"])

    for l in listings:
        print l.print_link()
        
