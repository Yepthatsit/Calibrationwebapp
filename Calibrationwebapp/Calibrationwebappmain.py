from flask import *
import os
import pandas as pd
import matplotlib.pyplot as plt
import scipy.interpolate
import numpy as np
import shutil
import math
aplication = Flask(__name__)
def writelist(file,list:list):
    dataline = ""
    for i in range(len(list)-1):
        dataline+= f"{list[i]} "
    dataline+= f"{list[-1]}\n"
    file.write(dataline)
@aplication.route("/")
def mainpage():
    return render_template("main.html")
'''
parametr request.method to rodzaj zapytania jakie to api dostaje z zewnątrz. otwarcie i zbieranie danych to GET a POST
ich wysyłanie na strone. musi dostać zapytanie post()
'''
'''strony pomiędzy sobą wysyłają jsony'''
@aplication.route("/api/upload",methods = ["POST"])
def uploadfiles():
    uploaddir = os.path.dirname(os.path.abspath(__file__)).replace("\\","/")
    file = request.files['fileInput']
    uploadedfiles = os.listdir(f"{uploaddir}/uploadedfiles")
    if not(file.filename in uploadedfiles):
        file.save(f"{uploaddir}/uploadedfiles/{file.filename}")
        return jsonify({"Exist":False})
    else:
        return jsonify({"Exist":True})
@aplication.route("/api/createsorted")
def create_sorted():
    if len(os.listdir(f'{os.path.dirname(os.path.abspath(__file__)).replace("\\","/")}/sorted')):
        return jsonify({"Sorted":False,"ready":False})
    if len(os.listdir(f'{os.path.dirname(os.path.abspath(__file__)).replace("\\","/")}/uploadedfiles'))!= 0 :
        path = f'{os.path.dirname(os.path.abspath(__file__)).replace("\\","/")}/uploadedfiles'
        datfiles = []
        allfiles = os.listdir(path)
        for file in allfiles:
            if ".dat" in file:
                datfiles.append(pd.read_csv(f"{path}/{file}",sep=" "))
        results = pd.concat(datfiles)
        sorted = results.sort_values("T_B[K]",ascending=False)
        sorted.to_csv(path_or_buf=f"{os.path.dirname(os.path.abspath(__file__)).replace("\\","/")}/sorted/sorted.dat",sep= " ", index= False)
        return jsonify({"Sorted":True,"ready":True})
    else:
        return jsonify({"Sorted":False,"ready":True})
@aplication.route("/api/renderresults")
def renderresults():
    generalpath = os.path.dirname(os.path.abspath(__file__)).replace('\\',"/")
    if len(os.listdir(f"{generalpath}/sorted")) == 1:
        ########################################### Miejsce na robienie wykresu interpolacje i tworzenie pliku kalibracyjnego
        #                       MODEL I ZDJECIE
        file = f"{generalpath}/sorted/sorted.dat"
        data = pd.read_csv(file, sep=" ")
        sensors = [ i for i in data.columns if '[Ohm]' in i and not '_B' in i]
        for sensor in sensors:
            plt.scatter(data.loc[:,"T_B[K]"],data.loc[:,sensor],c="g",s=5,label = "Measured values")
            a = np.linspace(min(data.loc[:,"T_B[K]"]),max(data.loc[:,"T_B[K]"]),5000)
            fitted = scipy.interpolate.interp1d(data.loc[:,"T_B[K]"],data.loc[:,sensor])
            fittedvalues = fitted(a)
            plt.plot(a,fittedvalues,c="r",label = "Extrapolated values")
            plt.legend()
            plt.xlabel("Temperature")
            plt.ylabel("Resistance")
            plt.xscale('log')
            plt.yscale('log')
            plt.savefig(fname = f"{generalpath}/foto/{sensor}.png")
            plt.clf()
            plt.close()
            #                       PLIKI KALIBRACYJNE
            #               Generowanie wartości
            #powienien szsukać przedziałów i po tym rozpoznawać
            values : list
            limits = (math.floor(max(data.loc[:,"T_B[K]"])),round(min(data.loc[:,"T_B[K]"]),1))
            if limits[0] >100:
                if limits[1] < 4:
                    values = [limits[0]] + list(range(limits[0]-int(str(limits[0])[-1]),100,-10)) + list(range(100,10,-5)) + list(range(10,4,-1)) + list(np.arange(4.0,limits[1]-0.1,-0.1).round(1))
                elif limits[1]<10 and limits[1]>4:
                    values = [limits[0]] + list(range(limits[0]-int(str(limits[0])[-1]),100,-10)) + list(range(100,10,-5)) + list(range(10,math.floor(limits[1]),-1))
                elif limits[1]<100 and limits[1] > 10:
                    values = [limits[0]] + list(range(limits[0]-int(str(limits[0])[-1]),100,-10)) + list(range(100,math.floor(limits[1]) - int(str(math.floor(limits[1]))[-1]),-5)) + [math.floor(limits[1])]
                else:
                    values = [limits[0]] + list(range(limits[0]-int(str(limits[0])[-1]),math.floor(limits[1]) - int(str(math.floor(limits[1]))[-1]),-10)) + [math.floor(limits[1])]
            elif limits[0] > 10:
                if limits[1] < 4:
                    values = [limits[0]] + list(range(limits[0]-int(str(limits[0])[-1]),10,-5)) + list(range(10,4,-1)) + list(np.arange(4.0,limits[1]-0.1,-0.1).round(1))
                elif limits[1]<10 and limits[1]>4:
                    values = [limits[0]] + list(range(limits[0]-int(str(limits[0])[-1]),10,-5)) + list(range(10,math.floor(limits[1]),-1))
                else:
                    values = [limits[0]] + list(range(limits[0]-int(str(limits[0])[-1]),math.floor(limits[1]) - int(str(math.floor(limits[1]))[-1]),-10)) + [math.floor(limits[1])]
            #
            #                      Tworzenie danych oraz zapis do plików
            #
            noumbers = list(range(1,len(values)+1))
            extrapolated_values = fitted(values)
            logValues = ["{:.9f}".format(math.log(i)) for i in extrapolated_values]
            lscifile = open(f"{generalpath}/Lakeshorefile/{sensor}.340","a")
            lscifile.write(f'Sensor Model:	-------\nSerial Number:	-------\nData Format:	4	(Log Ohms/Kelvin)\nSetPoint Limit:	{values[0]}	(Kelvin)\nTemperature coefficient:  ---------\nNumber of Breakpoints:	{len(values)}\n\nNo.	Units	Temperature (K)\n\n')
            for num,logval, temp in zip(noumbers,logValues,values):
                lscifile.write(f"{num} {logval} {temp}\n")
            lscifile.close()
        ###########################################################
        #                       Tworzenie zipów
        shutil.make_archive(base_name=f"{generalpath}/archives_to_be_sent/Images",format="zip",root_dir=f"{generalpath}/foto")
        shutil.make_archive(base_name=f"{generalpath}/archives_to_be_sent/LSCIfiles",format="zip",root_dir=f"{generalpath}/Lakeshorefile")
        return jsonify({"Rendered":True})
    else:
        return jsonify({"Rendered":False})
@aplication.route("/api/sendimage")
def sendimage():
    dir = f"{os.path.dirname(os.path.abspath(__file__)).replace('\\',"/")}/archives_to_be_sent/Images.zip"
    if os.path.exists(dir):
        return send_file(dir)
    else:
        return "Please render first"
@aplication.route("/api/LSCIFILE")
def sendLSCIfile():
    #zzipować pliki i wyslać zip
    dir = f"{os.path.dirname(os.path.abspath(__file__)).replace('\\',"/")}/archives_to_be_sent/LSCIfiles.zip"
    if os.path.exists(dir):
        return send_file(dir)
    else:
        return "Please render first"
@aplication.route("/api/clear")
def clearfiles():
    foldertoclear = ["foto","Lakeshorefile","sorted","archives_to_be_sent","uploadedfiles"]
    mainpath = os.path.dirname(os.path.abspath(__file__)).replace('\\','/')
    for foldername in foldertoclear:
        files = os.listdir(f"{mainpath}/{foldername}")
        if len(files):
            for  file in files:
                os.remove(f"{mainpath}/{foldername}/{file}")
    return jsonify({"Cleared":True})
if __name__ == "__main__":
    #to jest server tylko dla developmentu fajny jak pisze i dokładam nowe rzeczy ale o wiele wolniejszy
    aplication.run(host="localhost",port=6009,debug=True)
    # tak powinnna vyć postawiona aplikacja finalnie. I TAK MA BYĆ HOSTOWANA!
    #from waitress import serve
    #serve(aplication,host = "localhost", port =6009)
