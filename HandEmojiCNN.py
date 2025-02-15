# -*- coding: utf-8 -*-

from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Conv2D, MaxPooling2D, ZeroPadding2D
from keras.optimizers import SGD,RMSprop,adam
from keras.utils import np_utils

from keras import backend as K
if K.backend() == 'tensorflow':
    import tensorflow
    #K.set_image_dim_ordering('tf')
else:
    import theano
    #K.set_image_dim_ordering('th')

'''Ideally we should have changed image dim ordering based on Theano or Tensorflow, but for some reason I get following error when I switch it to 'tf' for Tensorflow.
	However, the outcome of the prediction doesnt seem to get affected due to this and Tensorflow gives me similar result as Theano.
	I didnt spend much time on this behavior, but if someone has answer to this then please do comment and let me know.
    ValueError: Negative dimension size caused by subtracting 3 from 1 for 'conv2d_1/convolution' (op: 'Conv2D') with input shapes: [?,1,200,200], [3,3,200,32].
'''
K.set_image_dim_ordering('th')
	
	
import numpy as np
#import matplotlib.pyplot as plt
import os

from PIL import Image
# SKLEARN
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
import json

import cv2
import matplotlib
#matplotlib.use("TkAgg")
from matplotlib import pyplot as plt

# input image dimensions
img_rows, img_cols = 200, 200

# number of channels
# For grayscale use 1 value and for color images use 3 (R,G,B channels)
img_channels = 1


# Batch_size to train
batch_size = 32

## Number of output classes (change it accordingly)
## eg: In my case I wanted to predict 4 types of gestures (Ok, Peace, Punch, Stop)
## NOTE: If you change this then dont forget to change Labels accordingly
nb_classes = 5

# Number of epochs to train (change it accordingly)
nb_epoch = 15  #25

# Total number of convolutional filters to use
nb_filters = 32
# Max pooling
nb_pool = 2
# Size of convolution kernel
nb_conv = 3

#%%
#  data
path = "./"
path1 = "./gestures"    #path of folder of images

## Path2 is the folder which is fed in to training model
path2 = './imgfolder_b'

WeightFileName = []

# outputs
output = ["OK", "NOTHING","PEACE", "PUNCH", "STOP"]
#output = ["PEACE", "STOP", "THUMBSDOWN", "THUMBSUP"]

jsonarray = {}

#%%
def update(plot):
    global jsonarray
    h = 450
    y = 30
    w = 45
    font = cv2.FONT_HERSHEY_SIMPLEX

    #plot = np.zeros((512,512,3), np.uint8)
    
    #array = {"OK": 65.79261422157288, "NOTHING": 0.7953541353344917, "PEACE": 5.33270463347435, "PUNCH": 0.038031660369597375, "STOP": 28.04129719734192}
    
    for items in jsonarray:
        mul = (jsonarray[items]) / 100
        #mul = random.randint(1,100) / 100
        cv2.line(plot,(0,y),(int(h * mul),y),(255,0,0),w)
        cv2.putText(plot,items,(0,y+5), font , 0.7,(0,255,0),2,1)
        y = y + w + 30

    return plot

#%% For debug trace
def debugme():
    import pdb
    pdb.set_trace()

#%%
# This function can be used for converting colored img to Grayscale img
# while copying images from path1 to path2
def convertToGrayImg(path1, path2):
    listing = os.listdir(path1)
    for file in listing:
        if file.startswith('.'):
            continue
        img = Image.open(path1 +'/' + file)
        #img = img.resize((img_rows,img_cols))
        grayimg = img.convert('L')
        grayimg.save(path2 + '/' +  file, "PNG")

#%%
def modlistdir(path, pattern = None):
    listing = os.listdir(path)
    retlist = []
    for name in listing:
        #This check is to ignore any hidden files/folders
        if pattern == None:
            if name.startswith('.'):
                continue
            else:
                retlist.append(name)
        elif name.endswith(pattern):
            retlist.append(name)
            
    return retlist


# Load CNN model
def loadCNN(bTraining = False):
    global get_output
    model = Sequential()
    
    
    model.add(Conv2D(nb_filters, (nb_conv, nb_conv),
                        padding='valid',
                        input_shape=(img_channels, img_rows, img_cols)))
    convout1 = Activation('relu')
    model.add(convout1)
    model.add(Conv2D(nb_filters, (nb_conv, nb_conv)))
    convout2 = Activation('relu')
    model.add(convout2)
    model.add(MaxPooling2D(pool_size=(nb_pool, nb_pool)))
    model.add(Dropout(0.5))

    model.add(Flatten())
    model.add(Dense(128))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))
    model.add(Dense(nb_classes))
    model.add(Activation('softmax'))
    
    #sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy'])
    
    # Model summary
    model.summary()
    # Model conig details
    model.get_config()
    
    if not bTraining :
        #List all the weight files available in current directory
        WeightFileName = modlistdir('.','.hdf5')
        if len(WeightFileName) == 0:
            print('Error: No pretrained weight file found. Please either train the model or download one from the https://github.com/asingh33/CNNGestureRecognizer')
            return 0
        else:
            print('Found these weight files - {}'.format(WeightFileName))
        #Load pretrained weights
        w = int(input("Which weight file to load (enter the INDEX of it, which starts from 0): "))
        fname = WeightFileName[int(w)]
        print("loading ", fname)
        model.load_weights(fname)

    # refer the last layer here
    layer = model.layers[-1]
    get_output = K.function([model.layers[0].input, K.learning_phase()], [layer.output,])
    
    
    return model

# This function does the guessing work based on input images
def guessGesture(model, img):
    global output, get_output, jsonarray
    #Load image and flatten it
    image = np.array(img).flatten()
    
    # reshape it
    image = image.reshape(img_channels, img_rows,img_cols)
    
    # float32
    image = image.astype('float32') 
    
    # normalize it
    image = image / 255
    
    # reshape for NN
    rimage = image.reshape(1, img_channels, img_rows, img_cols)
    
    # Now feed it to the NN, to fetch the predictions
    #index = model.predict_classes(rimage)
    #prob_array = model.predict_proba(rimage)
    
    prob_array = get_output([rimage, 0])[0]
    
    #print prob_array
    
    d = {}
    i = 0
    for items in output:
        d[items] = prob_array[0][i] * 100
        i += 1
    
    # Get the output with maximum probability
    import operator
    
    guess = max(d.items(), key=operator.itemgetter(1))[0]
    prob  = d[guess]

    if prob > 60.0:
        #print(guess + "  Probability: ", prob)

        #Enable this to save the predictions in a json file,
        #Which can be read by plotter app to plot bar graph
        #dump to the JSON contents to the file
        
        #with open('gesturejson.txt', 'w') as outfile:
        #    json.dump(d, outfile)
        jsonarray = d
                
        return output.index(guess)

    else:
        # Lets return index 1 for 'Nothing' 
        return 1
