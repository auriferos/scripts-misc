#!/usr/bin/python


import argparse
import pickle
import indeed
import os
import notifier

class archive:

    # an archive is useful if we want to run this as a chron job, and dont
    # want prior results displayed again
    # Eventually, maybe we'll figure out a low effort means of tracking 
    # what i've actually applied to or dismissed, instead of just 'viewed'    

        def __init__(self):
        self.class_archive={}
        self.home=os.environ['HOME']+'/jobhuntr/'
        if os.path.isfile(self.home+'archive.pkl'):
            with open(self.home+'archive.pkl', 'r') as file:
                self.class_archive=pickle.load(file)    

            i=0
            for key in self.class_archive.keys():
                i+=1            
    

        def push_archive(self,url):
        self.class_archive[str(url)]=True

    def query_archive(self,url):

        if url in self.class_archive:
            '''kinda redundant; we only store true, so if there- 
            is a key, then that implies the key is True; still,
            simply checking for the existance of a key seems sloppy.
            This way, we can later revert values to false 
            (in case we want to later revert/change behavior,
            or perhaps store a 'last viewed' instead of a bool?)
            '''
            
            return self.class_archive[url]
        else:
            return False


    def commit(self):
        with open(self.home+'archive.pkl', 'w') as handle:
            pickle.dump(self.class_archive,handle)
            handle.close()


def thresher(listings, filter_terms):
    #removing entries from listing
    assert type(listings) is dict
    assert type(filter_terms) is list
    chaff=[]
    for listing in listings:
        assert type(listings[listing]) is list
        if any (term in listings[listing][0] for term in filter_terms):
            chaff.append(listing)

    for trash in chaff:
            del listings[trash]

    return listings


def main():

    main_list=[]
    #just in case I want to add flags later...
    parser = argparse.ArgumentParser(description="Template script tool")
    parser.add_argument('-f', help='takes arbitrary input')
    parser.add_argument('-b', action='store_true', help='binary flag')
    args=parser.parse_args()

    #lets keep track of what we've already applied to    
    history=archive()    

    cwd=os.environ['HOME']+'/jobhuntr/'
    filter_terms=open(cwd+'filter_terms.txt')    
    search_terms=open(cwd+'terms.txt')
    areas=open(cwd+'zipcodes.txt')
    filter_terms_list=[]
    
    for term in filter_terms.read().splitlines().lower():
        filter_terms_list.append(term)

    for term in search_terms.readlines().lower():
        for location in areas.readlines().lower(): 
            #indeed section
            results=indeed.search_indeed(term,2,int(location))
            results=thresher(results,filter_terms_list)
            main_list.append(results)

    filter_terms.close()
    search_terms.close()
    areas.close()
        
    
    received=notifier.sendNotice(main_list,history)

    #save
    if received:
        history.commit()    


if __name__ == "__main__":
        main()
