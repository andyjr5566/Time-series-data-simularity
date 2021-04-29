import flask
import json
import pandas as pd
import numpy as np
import random
from dtaidistance import dtw
import datetime
app = flask.Flask(__name__)
app.config["DEBUG"] = False

def unix_timestamp(Range):
    R = Range.split(' ~ ')
    t1 = R[0].split('/')
    t2 = R[1].split('/')
    t1 = datetime.datetime(int(t1[2]),int(t1[0]),int(t1[1]))
    t2 = datetime.datetime(int(t2[2]),int(t2[0]),int(t2[1]))

    return [int(t1.timestamp()), int(t2.timestamp())]

def measureDistance(x, y, end = False):
    x, y = np.array(x), np.array(y)
    x = (x - x.min()) / (x.max() - x.min())

    da = np.concatenate((x, y), axis=0)
    re = dtw.distance_matrix_fast(da, window = 3, block=((0,1),(0,len(da))), compact=True, parallel = True)

    if end == True:
        return re.index(min(re))
    
    keep_index = np.where(re < np.nanpercentile(re, 20))[0]

    return keep_index

def url_value(value):
    sequence = value.split(",")
    clipNum = len(sequence)
    sequence = np.array(list(map(float, sequence)))
    sequence = sequence[np.newaxis,:]
    return sequence, clipNum

with open('StockData.json', 'r') as json_file:  
    h = json.load(json_file)

dataBase = pd.DataFrame(h)
y = np.vstack(dataBase['Curve'])


@app.route('/', methods=['GET'])

def home():


    return '''
<!doctype html>
<title>Andy's api</title>
<h1>Measure Distance</h1>
<body>
To use this api, send stock data through url. 
<br><br>
This api has three route: <br>
1. /measure/ (sequence) <br>
2. /measure2/ (sequence) <br>
3. /measureResult/ (sequence) <br><br>

P.S. (sequence) is the input of stock data that you want to compare with. <br>
The format is sting which combine with numbers and comma (Need to normalize beforehead). The maximun data can be fit in is 30.<br>
ex. The url can be like: http://127.0.0.1:5000/measure/0.387,0.455,0.328,0.236,0.31,0.154,0.27 <br><br>

<h1>How to use?</h1>
1.  Go to route 1 and replace (sequence) to stock data with currect format.<br>
This step will initialize, then select the top 20% data from the database that simular to the sequence that you input.<br><br>
2.  Go to route 2 for another selection from previous results from step 1, <br>
    Otherwise, go to route 3 to get the final result, which is the most simular curve from your sequence.<br>
    In step 3, you'll get a dictionary written as json format. The content is the name of the company, the curve and the range of date of the curve. <br><br>
3.  Go to route 1 to start another serch and so on.

</body> 

'''

@app.route('/measure/<sequence>')
def measure(sequence):
    x, clipNum = url_value(sequence)
    y1 = y[:,:clipNum]
    index = measureDistance(x, y1)

    global y2, dataBaseEdit
    y2 = y[index]
    dataBaseEdit = dataBase.loc[index]
    dataBaseEdit.index = range(len(dataBaseEdit.index))
    
    return str(len(dataBaseEdit.index)) + ' data left'

@app.route('/measure2/<sequence>')
def measure2(sequence):
    global y2, dataBaseEdit
    x, clipNum = url_value(sequence)
    y1 = y2[:,:clipNum]
    index = measureDistance(x, y1)
    y2 = y2[index]
    dataBaseEdit = dataBaseEdit.loc[index]
    dataBaseEdit.index = range(len(dataBaseEdit.index))
    
    return str(len(dataBaseEdit.index)) + ' data left'

@app.route('/measureResult/<sequence>')
def measureTrue(sequence):
    global y2, dataBaseEdit
    x, clipNum = url_value(sequence)
    y1 = y2[:,:clipNum]
    index = measureDistance(x, y1, end = True)
    y2 = y2[index]
    dataBaseEdit = dataBaseEdit.loc[index]
    dataBaseEdit['Unix Time Stamp'] = unix_timestamp(dataBaseEdit['Range'])
    return dataBaseEdit.to_dict()
app.run(threaded=True)

