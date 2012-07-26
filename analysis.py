#!/usr/bin/python

############################################################################
## title: analysis.py
## description: processes an input .csv from process.py
##              and returns a .csv file of results
## author: Joseph Kelly
## date of first edit: 07/20/2012
## date of last edit:  07/24/2012
############################################################################

import csv
import os
import sys
from scipy.stats import t
from numpy import power
from math import sqrt
from numpy import mean,std
inputfn = sys.argv[1]
#inputfn = "../data/test.txt"

##this function processes text file and produces dict containing data
def dataproc():
    ##open and parse file and store data
    
    f = open(inputfn, 'r')
    data = {}
    for line in f:   
        ##strip line if null reset some vars
        tmp = line.strip().split(":")
        if(tmp[0] == "push_id"):
            push_id = tmp[1]
            data[push_id] = {}

        if(tmp[0] == "page"):
            page = tmp[1]

        if(tmp[0] == "push_x1_replicates"):
            obs = eval(tmp[1])
            del obs[0]
            data[push_id][page] = obs
    f.close()
    return(data)



"""
here p is a list of floats of the form [pvalue for page 1, pvalue for page 2, ..
pvalue for page 100] and q is a float (recommended 0.1)
"""
def rejector( p, q ):
    #setup useful vars
    N = len(p)
    index = range(0,N)
    pindex = zip(p,index)
    sortedp = sorted(pindex)
    
    #find cutoff for rejection
    cutoff = [(i+1)*q/N for i in index]
    indicator = 0
    for i in index:
        if(sortedp[i][0] < cutoff[i]):
            indicator = i + 1

    #reject/fail to reject
    status = ['reject']*indicator + ['accept']*(N-indicator)
    output = range(0,N)
    for i in index:
        output[sortedp[i][1]] = status[i]

    return ({'status':output,'count':indicator})


"""
does a one sided t-test and returns pvalue
"""
def ttest(x1,x2):
    n1 = len(x1)
    n2 = len(x2)

    m1 = mean(x1)
    m2 = mean(x2)

    s1 = std(x1,ddof=1)
    s2 = std(x2,ddof=1)
    
    
    spooled        = sqrt( power(s1,2)/n1 + power(s2,2)/n2)
    tt             = (m1-m2)/spooled
    df_numerator   = power( power(s1,2)/n1 + power(s2,2)/n2 , 2 )
    df_denominator = power( power(s1,2)/n1 ,2)/(n1-1) + power( power(s2,2)/n2 ,2)/(n2-1)
    df             = df_numerator / df_denominator

    t_distribution = t(df)
    prob = 1 - t_distribution.cdf(tt)
    return prob

#main
#setup useful variables
count = []
datadict = dataproc()
pushes = datadict.keys()
pushes.sort()
pages = datadict[pushes[0]].keys()
goodpages = dict.fromkeys(pages,pushes[0])
##delete first push as no parent data
del pushes[0]

##loop through and run t-test
for push in pushes:
    pvalues = []
    for page in pages:
        x1 = datadict[push][page]
        x2 = datadict[goodpages[page]][page]
        pvalues.append(ttest(x1,x2))

    output = rejector(pvalues,0.05)
    count.append(output['count'])
    
    
    ##if didn't fail then change good pages
    for i in range(0,len(output['status'])):
        if(output['status'][i] == 'accept'):
            goodpages[pages[i]] = push

##write output
datafn = inputfn + '_python_results.csv'
try:
    os.remove(datafn)
except:
    pass
processWriter = csv.writer(open(datafn,'wb'),delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)

processWriter.writerow(pushes)
processWriter.writerow(count)

