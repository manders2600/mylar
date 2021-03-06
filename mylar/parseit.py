#  This file is part of Mylar.
#
#  Mylar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mylar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mylar.  If not, see <http://www.gnu.org/licenses/>.


from bs4 import BeautifulSoup 
import urllib2 
import re 
import helpers 
import logger 
import datetime 
from decimal import Decimal 
from HTMLParser import HTMLParseError

def GCDScraper(ComicName, ComicYear, Total, ComicID):
    NOWyr = datetime.date.today().year
    if datetime.date.today().month == 12:
        NOWyr = NOWyr + 1
        logger.fdebug("We're in December, incremented search Year to increase search results: " + str(NOWyr))
    comicnm = ComicName
    comicyr = ComicYear
    comicis = Total
    comicid = ComicID
    print ( "comicname: " + str(comicnm) )
    print ( "comicyear: " + str(comicyr) )
    print ( "comichave: " + str(comicis) )
    print ( "comicid: " + str(comicid) )
    comicnm = re.sub(' ', '+', comicnm)
    input = 'http://www.comics.org/search/advanced/process/?target=series&method=icontains&logic=False&order2=date&order3=&start_date=' + str(comicyr) + '-01-01&end_date=' + str(NOWyr) + '-12-31&series=' + str(comicnm) + '&is_indexed=None'
    response = urllib2.urlopen ( input )
    soup = BeautifulSoup ( response)
    cnt1 = len(soup.findAll("tr", {"class" : "listing_even"}))
    cnt2 = len(soup.findAll("tr", {"class" : "listing_odd"}))

    cnt = int(cnt1 + cnt2)

    #print (str(cnt) + " results")

    resultName = []
    resultID = []
    resultYear = []
    resultIssues = []
    resultURL = None
    n_odd = -1
    n_even = -1
    n = 0
    while ( n < cnt ):
        if n%2==0:
            n_even+=1
            resultp = soup.findAll("tr", {"class" : "listing_even"})[n_even]
        else:
            n_odd+=1
            resultp = soup.findAll("tr", {"class" : "listing_odd"})[n_odd]
        rtp = resultp('a')[1]
        resultName.append(helpers.cleanName(rtp.findNext(text=True)))
        #print ( "Comic Name: " + str(resultName[n]) )
        fip = resultp('a',href=True)[1]
        resultID.append(fip['href'])
        #print ( "ID: " + str(resultID[n]) )

        subtxt3 = resultp('td')[3]
        resultYear.append(subtxt3.findNext(text=True))
        resultYear[n] = resultYear[n].replace(' ','')
        subtxt4 = resultp('td')[4]
        resultIssues.append(helpers.cleanName(subtxt4.findNext(text=True)))
        resiss = resultIssues[n].find('issue')
        resiss = int(resiss)
        resultIssues[n] = resultIssues[n].replace('','')[:resiss]
        resultIssues[n] = resultIssues[n].replace(' ','')
        #print ( "Year: " + str(resultYear[n]) )
        #print ( "Issues: " + str(resultIssues[n]) )
        CleanComicName = re.sub('[\,\.\:\;\'\[\]\(\)\!\@\#\$\%\^\&\*\-\_\+\=\?\/]', '', comicnm)
        CleanComicName = re.sub(' ', '', CleanComicName).lower()
        CleanResultName = re.sub('[\,\.\:\;\'\[\]\(\)\!\@\#\$\%\^\&\*\-\_\+\=\?\/]', '', resultName[n])        
        CleanResultName = re.sub(' ', '', CleanResultName).lower()
        #print ("CleanComicName: " + str(CleanComicName))
        #print ("CleanResultName: " + str(CleanResultName))
        if CleanResultName == CleanComicName or CleanResultName[3:] == CleanComicName:
        #if resultName[n].lower() == helpers.cleanName(str(ComicName)).lower(): 
            #print ("n:" + str(n) + "...matched by name to Mylar!")
            #this has been seen in a few instances already, so trying to adjust.
            #when the series year is 2011, in gcd it might be 2012 due to publication
            #dates overlapping between Dec/11 and Jan/12. Let's accept a match with a 
            #1 year grace space, and then pull in the first issue to see the actual pub
            # date and if coincides with the other date..match it.
            if resultYear[n] == ComicYear or resultYear[n] == str(int(ComicYear)+1): 
                #print ("n:" + str(n) + "...matched by year to Mylar!")
                #print ( "Year: " + str(resultYear[n]) )
                #Occasionally there are discrepancies in comic count between
                #GCD and CV. 99% it's CV not updating to the newest issue as fast
                #as GCD does. Therefore, let's increase the CV count by 1 to get it
                #to match, any more variation could cause incorrect matching.
                #ie. witchblade on GCD says 159 issues, CV states 161.
                if int(resultIssues[n]) == int(Total) or int(resultIssues[n]) == int(Total)+1 or (int(resultIssues[n])+1) == int(Total):
                    #print ("initial issue match..continuing.")
                    if int(resultIssues[n]) == int(Total)+1:
                        issvariation = "cv"
                    elif int(resultIssues[n])+1 == int(Total):
                        issvariation = "gcd"
                    else:
                        issvariation = "no"
                        #print ("n:" + str(n) + "...matched by issues to Mylar!")
                        #print ("complete match!...proceeding")
                    TotalIssues = resultIssues[n]
                    resultURL = str(resultID[n])
                    rptxt = resultp('td')[6]
                    resultPublished = rptxt.findNext(text=True)
                    #print ("Series Published: " + str(resultPublished))
                    break
                
        n+=1
    # it's possible that comicvine would return a comic name incorrectly, or gcd
    # has the wrong title and won't match 100%...
    # (ie. The Flash-2011 on comicvine is Flash-2011 on gcd)
    # this section is to account for variations in spelling, punctuation, etc/
    basnumbs = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12}
    if resultURL is None:
        #search for number as text, and change to numeric
        for numbs in basnumbs:
            #print ("numbs:" + str(numbs))
            if numbs in ComicName.lower():
                numconv = basnumbs[numbs]
                #print ("numconv: " + str(numconv))
                ComicNm = re.sub(str(numbs), str(numconv), ComicName.lower())
                #print ("comicname-reVISED:" + str(ComicNm))
                return GCDScraper(ComicNm, ComicYear, Total, ComicID)
                break
        if ComicName.lower().startswith('the '):
            ComicName = ComicName[4:]
            return GCDScraper(ComicName, ComicYear, Total, ComicID)        
        if ':' in ComicName: 
            ComicName = re.sub(':', '', ComicName)
            return GCDScraper(ComicName, ComicYear, Total, ComicID)
        if '-' in ComicName:
            ComicName = re.sub('-', ' ', ComicName)
            return GCDScraper(ComicName, ComicYear, Total, ComicID)
        if 'and' in ComicName.lower():
            ComicName = ComicName.replace('and', '&')
            return GCDScraper(ComicName, ComicYear, Total, ComicID)        
        return 'No Match'
    #vari_loop = 0
    return GCDdetails(comseries=None, resultURL=resultURL, vari_loop=0, ComicID=ComicID, TotalIssues=TotalIssues, issvariation=issvariation, resultPublished=resultPublished)


def GCDdetails(comseries, resultURL, vari_loop, ComicID, TotalIssues, issvariation, resultPublished):

    gcdinfo = {}
    gcdchoice = []
    gcount = 0
    i = 0
    if vari_loop > 1:
        resultPublished = "Unknown"

    if vari_loop == 99: vari_loop = 1

    while (i <= vari_loop):
        if vari_loop > 0:
            try:
                boong = comseries['comseries'][i]
            except IndexError:
                break
            resultURL = boong['comseriesID']
            ComicID = boong['comicid']
            TotalIssues+= int(boong['comseriesIssues'])
        else: 
            resultURL = resultURL
            # if we're here - it means it's a mismatched name.
            # let's pull down the publication date as it'll be blank otherwise
            inputMIS = 'http://www.comics.org' + str(resultURL)
            resp = urllib2.urlopen ( inputMIS )
            soup = BeautifulSoup ( resp )

            parsed = soup.find("div", {"id" : "series_data"})
            subtxt3 = parsed.find("dd", {"id" : "publication_dates"})
            resultPublished = subtxt3.findNext(text=True).rstrip()
            #print ("pubdate:" + str(resultPublished))
            coverst = soup.find("div", {"id" : "series_cover"})
            if coverst < 0: 
                gcdcover = "None"
            else:
                subcoverst = coverst('img',src=True)[0]
                gcdcover = subcoverst['src']

        #print ("resultURL:" + str(resultURL))
        #print ("comicID:" + str(ComicID))
        input2 = 'http://www.comics.org' + str(resultURL) + 'details/'
        resp = urllib2.urlopen ( input2 )
        soup = BeautifulSoup ( resp )

        #for newer comics, on-sale date has complete date...
        #for older comics, pub.date is to be used

        type = soup.find(text=' On-sale date ')
        if type:
            #print ("on-sale date detected....adjusting")
            datetype = "on-sale"
        else:
            #print ("pub date defaulting")
            datetype = "pub"

        cnt1 = len(soup.findAll("tr", {"class" : "row_even_False"}))
        cnt2 = len(soup.findAll("tr", {"class" : "row_even_True"}))

        cnt = int(cnt1 + cnt2)

        #print (str(cnt) + " Issues in Total (this may be wrong due to alternate prints, etc")

        n_odd = -1
        n_even = -1
        n = 0
        PI = "1.00"
        altcount = 0
        while ( n < cnt ):       
            if n%2==0:
                n_odd+=1
                parsed = soup.findAll("tr", {"class" : "row_even_False"})[n_odd]
                ntype = "odd"
            else:
                n_even+=1
                ntype = "even"
                parsed = soup.findAll("tr", {"class" : "row_even_True"})[n_even]
            subtxt3 = parsed.find("a")
            ParseIssue = subtxt3.findNext(text=True)

            fid = parsed('a',href=True)[0]
            resultGID = fid['href']
            resultID = resultGID[7:-1]
            #print ( "ID: " + str(resultID) )

            if ',' in ParseIssue: ParseIssue = re.sub("\,", "", ParseIssue)
            isslen = ParseIssue.find(' ')
            #if 'isslen' exists, it means that it's an alternative cover.
            #however, if ONLY alternate covers exist of an issue it won't work.
            #let's use the FIRST record, and ignore all other covers for the given issue.
            isschk = ParseIssue[:isslen]
            #check if decimal or '1/2' exists or not, and store decimal results
            halfchk = "no"
            if '.' in isschk:
                isschk_find = isschk.find('.')
                isschk_b4dec = isschk[:isschk_find]
                isschk_decval = isschk[isschk_find+1:]
            elif '/' in isschk:
                ParseIssue = "0.50"
                isslen = 0
                halfchk = "yes"
            else:
                isschk_decval = ".00"

            if isslen > 0:
                isschk = ParseIssue[:isslen]
                isschk2 = str(isschk) + isschk_decval
                #logger.fdebug("isschk: " + str(isschk) + " ...isschk2: " + str(isschk2))
                if 'a' in isschk or 'b' in isschk or 'c' in isschk:
                    isschk2 = ParseIssue[:isslen-1] + isschk_decval
                    #altcount == 2
                ParseIssue = str(isschk2)
                #logger.fdebug("Alt.cover found = " + str(isschk2))
                if str(PI) == str(isschk2):
                    #logger.fdebug("matched on PI: " + str(PI) + " .. and isschk2: " + str(isschk2))
                    if altcount == 0:
                        #logger.fdebug("first occurance - marking and continuing..." + str(isschk2))
                        #this handles the first occurance..
                        ParseIssue = str(isschk2)
                        PI = str(isschk2)
                        altcount = 1
                    else:
                        #logger.fdebug("Using only first record for issue - ignoring further alternate matches")
                        ParseIssue = "this is wrong"
                        altcount+=1
                else:
                    #logger.fdebug("issues didn't match.")
                    altcount = 1
                    ParseIssue = str(isschk) + isschk_decval
            else:
                if halfchk == "yes": pass
                else: 
                    ParseIssue = ParseIssue + isschk_decval
                #print ("no alt.cover detected for - " + str(ParseIssue))
                altcount = 1
            if (altcount == 1):
                #logger.fdebug("adding issue to db : " + str(ParseIssue))
                # in order to get the compare right, let's decimialize the string to '.00'.
                gcdinfo['ComicIssue'] = ParseIssue
                #print "Issue: " + str(ParseIssue)
                #^^ will retrieve issue
                #if datetype == "on-sale":
                subtxt1 = parsed('td')[2]
                ParseDate = subtxt1.findNext(text=True)
                pdlen = len(ParseDate)
                #print "sale-date..ParseDate:" + str(ParseDate)
                #print ("Parsed Date length: " + str(pdlen))
                if len(ParseDate) < 7:
                    subtxt3 = parsed('td')[0]
                    ParseDate = subtxt3.findNext(text=True)               
                    #print "pub-date..ParseDate:" + str(ParseDate)
                    if ParseDate == ' ':
                        #default to empty so doesn't error out.
                        ParseDate = "0000-00-00"
                #ParseDate = ParseDate.replace('?','')
                ParseDate = ParseDate.replace(' ','')
                gcdinfo['ComicDate'] = ParseDate
                #^^ will retrieve date #
                if not any(d.get('GCDIssue', None) == str(gcdinfo['ComicIssue']) for d in gcdchoice):
                    #logger.fdebug("adding: " + str(gcdinfo['ComicIssue']))
                    if ComicID[:1] == "G":
                        gcdchoice.append({
                            'GCDid':                ComicID,
                            'IssueID':              resultID,
                            'GCDIssue':             gcdinfo['ComicIssue'],
                            'GCDDate':              gcdinfo['ComicDate']
                            })
                        gcount+=1
                    else:
                        gcdchoice.append({
                            'GCDid':                ComicID,
                            'GCDIssue':             gcdinfo['ComicIssue'],
                            'GCDDate':              gcdinfo['ComicDate']
                            })

                    gcdinfo['gcdchoice'] = gcdchoice

                else:
                    pass
                    #logger.fdebug("Duplicate issue detected in DB - ignoring subsequent issue # " + str(gcdinfo['ComicIssue']))

                PI = ParseIssue
        #else:
            # -- this needs a rework --
            # if issue only has alternative covers on comics.org, it won't match
            # and will cause the script to return a cannot retrieve..
            #compare previous issue to current issue (to help with alt.cover count)
         #   PI = ParseIssue
         #   altcount+=1
         #   print ("alternate issue - ignoring")
        #altcount = 0
            n+=1
        i+=1
    gcdinfo['gcdvariation'] = issvariation
    if ComicID[:1] == "G":
        gcdinfo['totalissues'] = gcount
    else:
        gcdinfo['totalissues'] = TotalIssues
    gcdinfo['ComicImage'] = gcdcover
    gcdinfo['resultPublished'] = resultPublished
    #print ("gcdvariation: " + str(gcdinfo['gcdvariation']))
    return gcdinfo
        ## -- end (GCD) -- ##

def GCDAdd(gcdcomicid):
    serieschoice = []
    series = {}
    logger.fdebug("I'm trying to find these GCD comicid's:" + str(gcdcomicid))
    for gcdid in gcdcomicid:
        logger.fdebug("looking at gcdid:" + str(gcdid))
        input2 = 'http://www.comics.org/series/' + str(gcdid)
        logger.fdebug("---url: " + str(input2))
        resp = urllib2.urlopen ( input2 )
        soup = BeautifulSoup ( resp )
        logger.fdebug("SeriesName section...")
        parsen = soup.find("span", {"id" : "series_name"})
        #logger.fdebug("series name (UNPARSED): " + str(parsen))
        subpar = parsen('a')[0]
        resultName = subpar.findNext(text=True)
        logger.fdebug("ComicName: " + str(resultName))
        #covers-start
        logger.fdebug("Covers section...")
        coverst = soup.find("div", {"id" : "series_cover"})
        if coverst < 0:
            gcdcover = "None"
            logger.fdebug("unable to find any covers - setting to None")
        else:
            subcoverst = coverst('img',src=True)[0]
            #logger.fdebug("cover (UNPARSED) : " + str(subcoverst))
            gcdcover = subcoverst['src']
        logger.fdebug("Cover: " + str(gcdcover))
        #covers end
        #publisher start
        logger.fdebug("Publisher section...")
        try:
            pubst = soup.find("div", {"class" : "item_data"})
            catchit = pubst('a')[0]

        except (IndexError, TypeError):
            pubst = soup.findAll("div", {"class" : "left"})[1]
            catchit = pubst.find("a")

        publisher = catchit.findNext(text=True)
        logger.fdebug("Publisher: " + str(publisher))
        #publisher end
        parsed = soup.find("div", {"id" : "series_data"})
        #logger.fdebug("series_data: " + str(parsed))
        #print ("parse:" + str(parsed))
        subtxt3 = parsed.find("dd", {"id" : "publication_dates"})
        #logger.fdebug("publication_dates: " + str(subtxt3))
        pubdate = subtxt3.findNext(text=True).rstrip()
        logger.fdebug("pubdate:" + str(pubdate))
        subtxt4 = parsed.find("dd", {"id" : "issues_published"})
        noiss = subtxt4.findNext(text=True)
        lenwho = len(noiss)
        lent = noiss.find(' ',2)
        lenf = noiss.find('(')
        stringit = noiss[lenf:lenwho]
        stringout = noiss[:lent]
        noissues = stringout.rstrip('  \t\r\n\0')
        numbering = stringit.rstrip('  \t\r\n\0')
        logger.fdebug("noissues:" + str(noissues))
        logger.fdebug("numbering:" + str(numbering))
        serieschoice.append({
               "ComicID":         gcdid,
               "ComicName":       resultName,
               "ComicYear" :        pubdate,
               "ComicIssues" :    noissues,
               "ComicPublisher" : publisher,
               "ComicCover" :     gcdcover
              })   
    series['serieschoice'] = serieschoice 
    return series


def ComChk(ComicName, ComicYear, ComicPublisher, Total, ComicID):
    comchkchoice = []
    comchoice = {}

    NOWyr = datetime.date.today().year
    if datetime.date.today().month == 12:
        NOWyr = NOWyr + 1
        logger.fdebug("We're in December, incremented search Year to increase search results: " + str(NOWyr))
    comicnm = ComicName
    comicyr = ComicYear
    comicis = Total
    comicid = ComicID
    comicpub = ComicPublisher
    print ( "comicname: " + str(comicnm) )
    print ( "comicyear: " + str(comicyr) )
    print ( "comichave: " + str(comicis) )
    print ( "comicpub: " + str(comicpub) )
    print ( "comicid: " + str(comicid) )
    # do 3 runs at the comics.org search to get the best results
    comicrun = []
    # &pub_name=DC
    # have to remove the spaces from Publisher or else will not work (ie. DC Comics vs DC will not match)
    # take the 1st word ;)
    #comicpub = comicpub.split()[0]
    # if it's not one of the BIG publisher's it might fail - so let's increase the odds.
    pubbiggies = [ 'DC', 
                   'Marvel',
                   'Image',
                   'IDW' ]
    uhuh = "no"
    for pb in pubbiggies:
        if pb in comicpub:
            #keep publisher in url if a biggie.    
            uhuh = "yes"
            print (" publisher match : " + str(comicpub))
            conv_pub = comicpub.split()[0]
            print (" converted publisher to : " + str(conv_pub))
    #1st run setup - leave it all as it is.
    comicrun.append(comicnm)
    cruncnt = 0
    #2nd run setup - remove the last character and do a broad search (keep year or else will blow up)
    if len(str(comicnm).split()) > 2:
        comicrun.append(' '.join(comicnm.split(' ')[:-1]))
        cruncnt+=1
    # to increase the likely hood of matches and to get a broader scope...
    # lets remove extra characters
    if re.sub('[\.\,\:]', '', comicnm) != comicnm:
        comicrun.append(re.sub('[\.\,\:]', '', comicnm))
        cruncnt+=1
    totalcount = 0
    cr = 0
    print ("cruncnt is " + str(cruncnt))
    while (cr <= cruncnt):
        print ("cr is " + str(cr))
        comicnm = comicrun[cr]
        #leaving spaces in will screw up the search...let's take care of it
        comicnm = re.sub(' ', '+', comicnm)
        print ("comicnm: " + str(comicnm))
        #input = 'http://www.comics.org/series/name/' + str(comicnm) + '/sort/alpha'
        if uhuh == "yes":
            publink = "&pub_name=" + str(conv_pub)
        if uhuh == "no":
            publink = "&pub_name="
#        input = 'http://www.comics.org/search/advanced/process/?target=series&method=icontains&logic=False&order2=date&order3=&start_date=' + str(comicyr) + '-01-01&end_date=' + str(NOWyr) + '-12-31&series=' + str(comicnm) + str(publink) + '&is_indexed=None'
        input = 'http://www.comics.org/search/advanced/process/?target=series&method=icontains&logic=False&keywords=&order1=series&order2=date&order3=&start_date=' + str(comicyr) + '-01-01&end_date=' + str(NOWyr) + '-12-31' + '&title=&feature=&job_number=&pages=&script=&pencils=&inks=&colors=&letters=&story_editing=&genre=&characters=&synopsis=&reprint_notes=&story_reprinted=None&notes=' + str(publink) + '&pub_notes=&brand=&brand_notes=&indicia_publisher=&is_surrogate=None&ind_pub_notes=&series=' + str(comicnm) + '&series_year_began=&series_notes=&tracking_notes=&issue_count=&is_comics=None&format=&color=&dimensions=&paper_stock=&binding=&publishing_format=&issues=&volume=&issue_title=&variant_name=&issue_date=&indicia_frequency=&price=&issue_pages=&issue_editing=&isbn=&barcode=&issue_notes=&issue_reprinted=None&is_indexed=None'
        print ("input: " + str(input))
        response = urllib2.urlopen ( input )
        soup = BeautifulSoup ( response)
        cnt1 = len(soup.findAll("tr", {"class" : "listing_even"}))
        cnt2 = len(soup.findAll("tr", {"class" : "listing_odd"}))

        try:
            cntit = soup.find("div", {"class" : "item_data"})
#            catchit = pubst('a')[0]

        except (IndexError, TypeError):
            cntit = soup.findAll("div", {"class" : "left"})[1]
#            catchit = pubst.find("a")

        truecnt = cntit.findNext(text=True)
        cnt = int(cnt1 + cnt2)
        print ("truecnt: " + str(truecnt))
        print ("cnt1: " + str(cnt1))
        print ("cnt2: " + str(cnt2))
        print (str(cnt) + " results")

        resultName = []
        resultID = []
        resultYear = []
        resultIssues = []
        resultPublisher = []
        resultURL = None
        n_odd = -1
        n_even = -1
        n = 0
        while ( n < cnt ):
            if n%2==0:
                n_even+=1
                resultp = soup.findAll("tr", {"class" : "listing_even"})[n_even]
            else:
                n_odd+=1
                resultp = soup.findAll("tr", {"class" : "listing_odd"})[n_odd]
            rtp = resultp('a')[1]
            resultName.append(helpers.cleanName(rtp.findNext(text=True)))
            print ( "Comic Name: " + str(resultName[n]) )

            pub = resultp('a')[0]
            resultPublisher.append(pub.findNext(text=True))
            print ( "Publisher: " + str(resultPublisher[n]) )

            fip = resultp('a',href=True)[1]
            resultID.append(fip['href'])
#            print ( "ID: " + str(resultID[n]) )

            subtxt3 = resultp('td')[3]
            resultYear.append(subtxt3.findNext(text=True))
            resultYear[n] = resultYear[n].replace(' ','')
            subtxt4 = resultp('td')[4]
            resultIssues.append(helpers.cleanName(subtxt4.findNext(text=True)))
            resiss = resultIssues[n].find('issue')
            resiss = int(resiss)
            resultIssues[n] = resultIssues[n].replace('','')[:resiss]
            resultIssues[n] = resultIssues[n].replace(' ','')
#            print ( "Year: " + str(resultYear[n]) )
#            print ( "Issues: " + str(resultIssues[n]) )
            print ("comchkchoice: " + str(comchkchoice))
#            if (cr == 0 and n == 0) or (comchkchoice is None):
#                print ("initial add.")
#                comchkchoice.append({
#                       "ComicID":         str(comicid),
#                       "ComicName":       str(resultName[n]),
#                       "GCDID":           str(resultID[n]),
#                       "ComicYear" :      str(resultYear[n]),
#                       "ComicPublisher" : str(resultPublisher[n]),
#                       "ComicIssues" :    str(resultIssues[n])
#                       })
            if not any(d.get('GCDID', None) == str(resultID[n]) for d in comchkchoice):
                print ( str(resultID[n]) + " not in DB...adding.")
                comchkchoice.append({
                       "ComicID":         str(comicid),
                       "ComicName":       str(resultName[n]),
                       "GCDID":           str(resultID[n]).split('/')[2],
                       "ComicYear" :      str(resultYear[n]),
                       "ComicPublisher" : str(resultPublisher[n]),
                       "ComicURL" :       "http://www.comics.org" + str(resultID[n]),
                       "ComicIssues" :    str(resultIssues[n])
                      })
            else:
                print ( str(resultID[n]) + " already in DB...skipping" ) 
            n+=1
        cr+=1
    totalcount= totalcount + cnt
    comchoice['comchkchoice'] = comchkchoice
    return comchoice, totalcount 

