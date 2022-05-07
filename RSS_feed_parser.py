import feedparser
import string
import time
import threading
from project_util import translate_html
from mtTkinter import *
from datetime import datetime
import pytz
import sys

#-----------------------------------------------------------------------

#======================
# Code for retrieving and parsing
# BBC and CNN News feeds
# Do not change this code
#======================

def process(url):
    """
    Fetches news items from the rss url and parses them.
    Returns a list of NewsStory-s.
    """
    feed = feedparser.parse(url)
    entries = feed.entries
    ret = []
    for entry in entries:
        guid = entry.guid
        title = translate_html(entry.title)
        link = entry.link
        #print(entry)
        description = translate_html(entry.description)
        pubdate = translate_html(entry.published)

        try:
            pubdate = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %Z")
            pubdate.replace(tzinfo=pytz.timezone("GMT"))
          #  pubdate = pubdate.astimezone(pytz.timezone('EST'))
          #  pubdate.replace(tzinfo=None)
        except ValueError:
            pubdate = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %z")

        newsStory = NewsStory(guid, title, description, link, pubdate)
        ret.append(newsStory)
    return ret

#======================
# Data structure design
#======================


# Class NewsStory, which stores all the relevant information regarding the parsed news.

class NewsStory(object):
    def __init__ (self, guid, title, description, link, pubdate):
        #Initializes all the attributes for the instance, which are:
        #guid - Globally unique identifier for the news story;
        #title - Tittle of the news;
        #description - A description of the story;
        #link - A link to more content;
        #pubdate - The date of publication.
        self.guid = guid
        self.title = title
        self.description = description
        self.link = link
        if pubdate.tzinfo == None:
            pubdate = pubdate.replace(tzinfo = pytz.timezone("EST"))
        self.pubdate = pubdate
    def get_guid(self):
        #Safely returns the guid for the news
        return self.guid
    def get_title(self):
        #Safely returns the title for the news
        return self.title
    def get_description(self):
        #Safely returns the new's description
        return self.description
    def get_link(self):
        #Safely returns the link for related news
        return self.link
    def get_pubdate(self):
        #Safely returns the publication date
        return self.pubdate
    


#======================
# Triggers
#======================

class Trigger(object):
    def evaluate(self, story):
        """
        Returns True if an alert should be generated
        for the given news item, or False otherwise.
        """
        # DO NOT CHANGE THIS!
        raise NotImplementedError

# PHRASE TRIGGERS


class PhraseTrigger(Trigger):
    def __init__ (self, phrase):
        #initializes the instance and transforms the phrase to lowercase
        self.phrase = phrase.lower()
    def is_phrase_in(self, input_string):
        #make sure the input string is lowercase
        input_string = input_string.lower()
        phrase = self.phrase
        
        #initializes an auxiliary string with all the punctuation
        aux_string = string.punctuation
        
        #remove all the punctuation from the string
        for letter in aux_string:
            input_string=input_string.replace(letter,' ')
            phrase = phrase.replace(letter,' ')
        #split the phrase and input into lists
        phrase_list = phrase.split()
        input_list = input_string.split()
        index_list = []
        
        #check every word in the phrase and verify whether it is in the input
        for word in phrase_list:
            try:
                index_list.append(input_list.index(word))
            except:
                return False
        
        for i in range(0,len(index_list)-1):
            if index_list[i+1]-index_list[i] != 1:
                return False
        return True
    
        


class TitleTrigger(PhraseTrigger):
    def __init__(self, phrase):
    	#initializes instance with a phrase
        PhraseTrigger.__init__(self, phrase)
    def evaluate(self, news):
    	#uses parent class method to evaluate phrase
        return(PhraseTrigger.is_phrase_in(self, news.get_title()))

class DescriptionTrigger(PhraseTrigger):
    def __init__(self, phrase):
    	#initializes class with a phrase
        PhraseTrigger.__init__(self, phrase)
    def evaluate(self, news):
    	#uses parent class method to evaluate phrase
        return(PhraseTrigger.is_phrase_in(self, news.get_description()))

# TIME TRIGGERS


class TimeTrigger(Trigger):
    def __init__(self, time):
    	#convert the date provided and add the timezone
        aux_datetime = datetime.strptime(time, "%d %b %Y %H:%M:%S")
        aux_datetime= aux_datetime.replace(tzinfo = pytz.timezone("EST"))
        #initializes time class
        self.publication_date = aux_datetime


class BeforeTrigger(TimeTrigger):
    def __init__(self, time):
    	#uses parent class to initialize attributes
        TimeTrigger.__init__(self, time)
    def evaluate(self, news):
    	#read publication date from news object
        news_date = news.get_pubdate()
        #verify if trigger date is greater than news_date
        if self.publication_date > news_date:
            return True
        else:
            return False
        
class AfterTrigger(TimeTrigger):
    def __init__(self, time):
    	#uses parent class to initialize attributes
        TimeTrigger.__init__(self, time)
    def evaluate(self, news):
    	#read publication date from news object
        news_date = news.get_pubdate()
        #verify if trigger date is less than news_date
        if self.publication_date < news_date:
            return True
        else:
            return False

# COMPOSITE TRIGGERS


class NotTrigger(Trigger):
    def __init__(self, trigger):
    	#creates an instance of the class with the trigger attribute.
        self.trig = trigger
        
    def evaluate(self,story):
    	#return the opposite of the inpute class
        return not self.trig.evaluate(story)
        



class AndTrigger(Trigger):
    def __init__(self, first_trigger, second_trigger):
    	#creates an instance of the class with the two triggers attributes.
        self.first_trigger = first_trigger
        self.second_trigger = second_trigger
        
    def evaluate(self, story):
    	#returns the result from the boolean operation "AND" between the two triggers.
        return self.first_trigger.evaluate(story) and self.second_trigger.evaluate(story)


class OrTrigger(Trigger):
    def __init__(self, first_trigger, second_trigger):
    	#creates an instance of the class with the two triggers attributes.
        self.first_trigger = first_trigger
        self.second_trigger = second_trigger
        
    def evaluate(self, story):
    	#returns the result from the boolean operation "AND" between the two triggers.
        return self.first_trigger.evaluate(story) or self.second_trigger.evaluate(story)


#======================
# Filtering
#======================

def filter_stories(stories, triggerlist):
    """
    Takes in a list of NewsStory instances.

    Returns: a list of only the stories for which a trigger in triggerlist fires.
    """

    filtered_stories = []
    
    #go through all the stories in the desired RSS feeds
    for story in stories:
    	#go through all the triggers in the desired trigger list
        for trigger in triggerlist:
        	#display the titles of all the stories in the CMD
            print(story.get_title())
            #verify whether the story triggers any of the filters
            if trigger.evaluate(story) == True:
                if story not in aux_stories:
                	#if the story triggers a filter and it is not already in the list, append it to the list
                    filtered_stories.append(story)
    #return the list of stories
    return filtered_stories



#======================
# User-Specified Triggers
#======================
def read_trigger_config(filename):
    """
    filename: the name of a trigger configuration file

    Returns: a list of trigger objects specified by the trigger configuration
        file.
    """
    # Reads the input file and get rid of the empty lines and those that start with '//'
    trigger_file = open(filename, 'r')
    lines = []
    for line in trigger_file:
        line = line.rstrip()
        if not (len(line) == 0 or line.startswith('//')):
            lines.append(line)
    
    #Creates an auxiliary dictionary for the filter names
    filter_dict = {"title":TitleTrigger, "description":DescriptionTrigger, "after": AfterTrigger,"before": BeforeTrigger, "not":NotTrigger, "and":AndTrigger, "or":OrTrigger}
    input_dict = {}
    ret_list = []
    
    #Goes through each line in the txt file
    for line in lines:
    	#Split the line into a list based on ','
        aux_line = line.split(',')
        #If the first word is not "ADD" and the filter is different from a "OR" and "AND", initiates the filter with the third word in the line
        if aux_line[0].lower() != "add" and (aux_line[1].lower() != "or" and aux_line[1].lower() != "and"):           
            input_dict[aux_line[0].lower()] = filter_dict[aux_line[1].lower()](aux_line[2].lower())
        #If the first word is not "ADD", but the filter is an OR or AND, initiates the filter with the third and fourth word in the line
        elif aux_line[0].lower() != "add" and (aux_line[1].lower() != "or" or aux_line[1].lower() != "and"):
            input_dict[aux_line[0].lower()] = filter_dict[aux_line[1].lower()](input_dict[aux_line[2].lower()],input_dict[aux_line[3].lower()])
        #If the first word is "ADD", add the filters to the list of filters to return.
        else:
            ret_list.append(input_dict[aux_line[1].lower()])
            ret_list.append(input_dict[aux_line[2].lower()])

    return(ret_list)



SLEEPTIME = 120 #seconds -- how often we poll

def main_thread(master):
    # A sample trigger list - you might need to change the phrases to correspond
    # to what is currently in the news
    try:
		#Read the filters and words to filter in the file triggers.txt
        triggerlist = read_trigger_config("triggers.txt")

        
        # HELPER CODE - you don't need to understand this!
        # Draws the popup window that displays the filtered stories
        # Retrieves and filters the stories from the RSS feeds
        frame = Frame(master)
        frame.pack(side=BOTTOM)
        scrollbar = Scrollbar(master)
        scrollbar.pack(side=RIGHT,fill=Y)

        t = "BBC & NY Times Top News"
        title = StringVar()
        title.set(t)
        ttl = Label(master, textvariable=title, font=("Helvetica", 18))
        ttl.pack(side=TOP)
        cont = Text(master, font=("Helvetica",14), yscrollcommand=scrollbar.set)
        cont.pack(side=BOTTOM)
        cont.tag_config("title", justify='center')
        button = Button(frame, text="Exit", command=root.destroy)
        button.pack(side=BOTTOM)
        guidShown = []
        def get_cont(newstory):
            if newstory.get_guid() not in guidShown:
                cont.insert(END, newstory.get_title()+"\n", "title")
                cont.insert(END, "\n---------------------------------------------------------------\n", "title")
                cont.insert(END, newstory.get_description())
                cont.insert(END, "\n*********************************************************************\n", "title")
                guidShown.append(newstory.get_guid())

        while True:

            print("Polling . . .", end=' ')
            # Get stories from Google's Top Stories RSS news feed
            stories = process("http://feeds.bbci.co.uk/news/rss.xml")

            # Get stories from Yahoo's Top Stories RSS news feed
            stories.extend(process("https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"))

            stories = filter_stories(stories, triggerlist)

            list(map(get_cont, stories))
            scrollbar.config(command=cont.yview)


            print("Sleeping...")
            time.sleep(SLEEPTIME)

    except Exception as e:
        print(e)


if __name__ == '__main__':
    root = Tk()
    root.title("Some RSS parser")
    t = threading.Thread(target=main_thread, args=(root,))
    t.start()
    root.mainloop()

