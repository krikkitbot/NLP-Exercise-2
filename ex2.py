import spacy
import en_core_web_sm
import urllib.request
import re

# Noun object that tracks # of informational/propositional (info)
# and eventuality (event) occurrences
class Noun:
    def __init__(self,type):
        # initialize with 1 occurrence as whichever type it occurred as
        if type == "info":
            self.info = 1
            self.event = 0
        elif type == "event":
            self.event = 1
            self.info = 0
        else:
            # obligatory error catching
            print("Error: Invalid type (",type,")")
            exit()
            
    # increment info count by 1
    def add_info_count(self):
        self.info += 1
            
    # same, but for event count
    def add_event_count(self):
        self.event += 1
            
    # return whether noun is informational, eventuality, or both
    def get_type(self):
        if self.info > 0:
            if self.event == 0:
                return "info"
            else:
                return "both"
        elif self.event > 0:
            return "event"
        else:
            return None
            
    # returns predominant type for polysemous cases
    def get_primary_type(self):
        if self.info > self.event:
            return "info"
        elif self.event > self.info:
            return "event"
        else:
            return "equal"

def get_texts(url_list):
    # create a list containing the text from each url and return it
    texts = []
    texts.append(urllib.request.urlopen(url_list[0]).read().decode("ASCII", "ignore"))
    for url in url_list[1:]:
        texts.append(urllib.request.urlopen(url).read().decode("utf-8"))
    return texts

# for removing chapter/verse numbers from bible
def remove_verse_nums(text):
    # chapter/verse numbers always have the format ###:###
    # this uses a regex to replace all such instances with a space
    return re.sub("\d{3}:\d{3}"," ",text)

def list_nouns(nouns):
    # create lists to sort nouns into
    only_info = []
    mainly_info = []
    equal = []
    mainly_event = []
    only_event = []
    
    for noun in nouns.keys():
        # get type of noun
        type = nouns[noun].get_type()
        # determine which list it belongs in and put it there
        if type == "info":
            only_info.append(noun)
        elif type == "event":
            only_event.append(noun)
        elif type == None:
            print("Error: Noun \"",noun,"\" has no type.")
            exit()
        else:
            primary_type = nouns[noun].get_primary_type()
            if primary_type == "info":
                mainly_info.append(noun)
            elif primary_type == "event":
                mainly_event.append(noun)
            else:
                equal.append(noun)
                
    # finally, print each list
    print("Exclusively informational nouns: ",only_info)
    print("Primarily informational nouns: ",mainly_info)
    print("Equally informational nouns and eventualities: ",equal)
    print("Primarily eventualities: ",mainly_event)
    print("Exclusively eventualities: ",only_event )

def main():
    # initialize nlp
    nlp = en_core_web_sm.load()
    nlp.max_length = 5000000
    # create list of text urls and get texts
    austen = "https://www.gutenberg.org/files/31100/31100.txt"
    reviews = "https://www.gutenberg.org/files/62369/62369-0.txt"
    bible = "https://www.gutenberg.org/cache/epub/8294/pg8294.txt"
    texts = get_texts([austen,reviews,bible])
    # remove verse numbers from bible
    texts[1] = remove_verse_nums(texts[1])
    # create spacy docs
    docs = [nlp(text, disable = "ner") for text in texts]
    # create dictionary to track nouns (word = key; Noun object = value)
    nouns = {}
    
    # iterate over docs
    for doc in docs:
        # iterate over tokens
        # stops three before the end to prevent out-of-bounds errors when examining context
        for i in range(1,len(doc)-3):
            # find nouns
            if doc[i].pos_ == "NOUN":
                noun = doc[i].text
                # check for eventualities such as "three-minute message"
                if doc[i-3].pos_ == "NUM" and doc[i-2].text == "-":
                    if noun in nouns:
                        nouns[noun].add_event_count()
                    else:
                        nouns[noun] = Noun("event")
                    continue
                # check for eventualities expressed through predicate
                # e.g., "the message lasted three minutes" or "message that lasted three minutes"
                if (doc[i+1].pos_ == "VERB" and doc[i+2].pos_ == "NUM") or (doc[i+1].text == "that" and doc[i+2].pos_ == "VERB" and doc[i+3].pos_ == "NUM"):
                    if noun in nouns:
                        nouns[noun].add_event_count()
                    else:
                        nouns[noun] = Noun("event")
                    continue
                # check for propositional complement clauses (headed by "that")
                # POS is checked to distinguish "that" as a subordinating conjunction
                #  from "that" as a relative pronoun
                if doc[i+1].text == "that" and doc[i+1].pos_ == "SCONJ":
                    if noun in nouns:
                        nouns[noun].add_info_count()
                    else:
                        nouns[noun] = Noun("info")
                    continue
    # list the nouns by type            
    list_nouns(nouns)
    
main()