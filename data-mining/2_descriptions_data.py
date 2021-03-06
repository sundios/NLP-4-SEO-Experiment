#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 12:33:33 2020

@author: margaretsant
"""



################ Webscraper to get descriptions for each URL: #################
from bs4 import BeautifulSoup
import requests
import pandas as pd

data = pd.read_csv("datasets/traffic_by_query.csv")
performance_data = pd.DataFrame(data['URL']).drop_duplicates()
performance_data['URL'] = performance_data['URL'].str.replace("'","")


#   keep data with URLs that are product pages:
#   performance_data = performance_data[performance_data['Page'].str.contains("/product/")]

#   remove rows with URLs that do not produce error code or have redirection:

for i in range(len(performance_data)):
    response = requests.get(performance_data['URL'].iloc[i], timeout = 100)
    if response.status_code != 200:
        performance_data = performance_data.drop(performance_data.index[i])
        continue
    for j in response.history:
        if j.status_code == 301:
            performance_data = performance_data.drop(performance_data.index[i])

#################### Build Webscraper with Beautiful Soup #####################
urls = performance_data["URL"].tolist()
titles = []
descriptions = []
for i in urls:
    response = requests.get(i, timeout = 100)
    content = BeautifulSoup(response.content, "html.parser")
    description = content.find('div', {"id":"tab-description"}).text
    descriptions.append(description)
    title = content.find('h1' , {"class":"product-title"}).text
    titles.append(title)

# create dataframe with url, title, description, date published
text_data = pd.DataFrame(list(zip(urls, titles, descriptions)), 
               columns =['URL', 'Title','Description']) 
#   pudlish date downloaded from wordpress

date_data = pd.read_csv("url-dates.csv")
#   figure our which urls match and which don't
#merged_date = pd.merge(text_data, date_data, on='URL', how='outer', indicator=True)

text_data = date_data.merge(text_data, on=['URL'], how='inner')


#################### Clean Text Data with NLP #################################
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

# import seaborn as sns
#%matplotlib inline
#%config InlineBackend.figure_format = 'retina'

#   removing punctuation
def remove_punctuation(text):
    '''a function for removing punctuation'''
    import string
    # replacing the punctuations with no space, 
    # which in effect deletes the punctuation marks 
    translator = str.maketrans('', '', string.punctuation)
    # return the text stripped of punctuation marks
    return text.translate(translator)

text_data['Description'] = text_data['Description'].apply(remove_punctuation)
text_data['Title'] = text_data['Title'].apply(remove_punctuation)
#dataset['Description'][1]

#   removing stopwords
sw = stopwords.words('english')
def stopwords(text):
    '''a function for removing the stopword'''
    # removing the stop words and lowercasing the selected words
    text = [word.lower() for word in text.split() if word.lower() not in sw]
    # joining the list of words with space separator
    return " ".join(text)

text_data['Description'] = text_data['Description'].apply(stopwords)
text_data['Title'] = text_data['Title'].apply(stopwords)

#   Stemming 
stemmer = SnowballStemmer("english")
def stemming(text):    
    '''a function which stems each word in the given text'''
    text = [stemmer.stem(word) for word in text.split()]
    return " ".join(text) 

text_data['Description'] = text_data['Description'].apply(stemming)
text_data['Title'] = text_data['Title'].apply(stemming)

#   Get Length of Text (might have a slight affect on Google search performance)
def length(text):    
    '''a function which returns the length of text'''
    return len(text)

text_data['Length'] = text_data['Description'].apply(length)

#################### Export Datasets #################################

#   merge performance data and text data:
performance_data = performance_data.rename(columns={"Page": "URL"})
dataset = pd.merge(text_data, performance_data, on='URL')

#   export
dataset.to_csv('datasets/text-and-traffic-data.csv')


