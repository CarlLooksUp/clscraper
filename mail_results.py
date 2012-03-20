import clparse
from automail import automail
from datetime import date
import os


listings =clparse.compile_listings("http://boston.craigslist.org/search/aap", 
                            bedrooms = '5', 
                            query = 'somerville|davis|porter|ball|tufts')

listings.sort(key=lambda listing: listing.price)
listings =clparse.sift_by_location(listings, ["somerville", "porter", "davis", 
                                              "ball", "tufts", "cambridge"])
subject = "Craigslist results for " + str(date.today())
body_text = ""
for listing in listings:
    body_text += listing.print_link() + "<br/>"

body_text += "<br/>Search terms: somerville, davis, porter, ball, tufts"

directory = os.path.dirname(__file__)
if not directory:
    directory = "."
settings_filename = directory + "/mail_settings.txt"

automail.send_email(automail.parse_settings(settings_filename),
                    subject, body_text, 'html')


