import pandas as pd
import numpy as np 
import datetime as dt
import pyodbc
import impyute
from sklearn import preprocessing


def get_data(well_name):
    # setting time interval as five days earlier from present
    # stime=str((dt.datetime.today()-dt.timedelta(5)).strftime('%Y-%m-%d'))
    # getting well id
    #well_name=(well_name)
    # making required tag's list
    list=[well_name+'S0001',well_name+'MI0001',well_name+'MSI0001',well_name+'MSUI0001',well_name+'PT0001']
    #list=[t1,t2,t3,t4,t5]
    # variables declaration for db connection
    server = 'SSHDB001' 
    database = 'CBMIP21BD' 
    table='CBM_SPLITDATA_HDA'
    username = 'IP21.USER' 
    password = 'ril@1234' 
    # connect to database
    conn=pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    # read data from sql server db and filtering respective tags  
    d1=pd.read_sql("select ItemID,ItemTimeStamp,ItemCurrentValue=convert(float,ItemCurrentValue),ItemQuality from " +table+ " where ItemTimeStamp >= '2019-07-26 00:00:00' and ItemTimeStamp < '2019-07-28 00:00:00' and ItemID in ('%s')"%("','".join(list)),conn)
    # pivot data
    d2=d1.pivot_table(index=pd.to_datetime(d1['ItemTimeStamp']),columns='ItemID',values='ItemCurrentValue')
    # Renaming columns with respective description
    #d2.columns=['RPM','Current','Speed','Torque','Tubing Pressure','Gas Flow to the Network']
    return d2

def clean(df):
    # replace -ve with 0
    df[df < 0] = 0
    return df

def sync(df):
    # data imputation
    imputed_data=impyute.imputation.ts.locf(df,axis=1)
    # converting index to timestamp
    imputed_data.index=pd.to_datetime(df.index)
    # find the difference between two consecutive 'ItemTimeStamp' and get the differenced value with high frequency
    n=int(imputed_data.index.to_series().diff().astype('timedelta64[m]').mode())
    # resample time series data based on the frequency
    d4=imputed_data.resample(dt.timedelta(minutes=n)).bfill()
    # normalization
    d4=pd.DataFrame(data=preprocessing.normalize(d4,axis=0),index=pd.to_datetime(df.index),columns=df.columns.str.rstrip())
    # dropping columns with all values zero  
    #resampled_data=d4.loc[:,(df!= 0).any(axis=0)]
    # renaming columns
    #resampled_data.columns=['RPM','Current','Speed','Torque','Tubing_Pressure','Gas Flow to the Network']
    return d4

def pump_on_or_off(df):
    # for each row checking the below condition and adding new column 'pump_on_or_off' with 1 if satisfied
    df.loc[(df['RPM'] > 10) & (df['Torque'] > 5) & (df['Current'] > 3),'pump_on_or_off'] = 1
    return df

def rpm_changed(df):
    # for each row checking below condition for two consecutive values difference and adding new column 'pump_on_or_off' with 1 if satisfied
    df.loc[(df.RPM.diff()<-10) | (df.RPM.diff()>10),'rpm_changed'] = 1
    return df

def n_days_since_start(df):
    # for each row checking 5 days earlier from it was 0 or 1
    df['n_days_since_start'] = df.pump_on_or_off.shift(5,freq='D').apply(lambda x: 1 if x==1 else 0)
    return df

def slope(n,df):
    # normalizing data
    norm_data=df
    # cols_to_norm = ['Tubing Pressure','Torque','Current']
    # norm_data[cols_to_norm] = norm_data[cols_to_norm].apply(lambda x: (x - x.min()) / (x.max() - x.min()))
    norm_data['Tubing_Pressure']=preprocessing.normalize(norm_data[['Tubing_Pressure']],axis=0)
    norm_data['Torque']=preprocessing.normalize(norm_data[['Torque']],axis=0)
    norm_data['Current']=preprocessing.normalize(norm_data[['Current']],axis=0)
    # converting index to timestamp
    norm_data.index=pd.to_datetime(df.index)
    # renaming columns and remove space at the end of column name
    norm_data.columns=df.columns.str.rstrip() 
    norm_data=norm_data.fillna(0)
    #setting window
    w=norm_data.rolling(int(60/n*24))
    # for each row of below mentioned column calculating slope by fitting regression line between that point to 1 day earlier to it
    norm_data['THP_Slope']=w['Tubing_Pressure'].apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
    norm_data['Torque_Slope']=w['Torque'].apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
    norm_data['Current_Slope']=w['Current'].apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])
    norm_data=norm_data.fillna(0)
    return norm_data
  
def annotate_tubing_failure(df,n):
    df=df[(df['THP_Slope'].rolling(int(60/n*24)).median().shift(int(60/n))<-0.1e-05) & (df['Torque_Slope'].rolling(int(60/n*24)).median().shift(int(60/n))<-0.5e-05) & (df['Current_Slope'].rolling(int(60/n*24)).median().shift(int(60/n))<-0.4e-06)]
    return df

def main():
    d=pd.read_excel("C:\\Users\\S.Nivedhitham\\SNivedhitha\\PCP Analytics\\data\\tag.xlsx",sheet_name='Well',usecols='A')
    l=list(d['Well'])
    for i in range(0,len(l)):
        df=get_data('SWS0615')
        df,n=sync(df)
        df.to_excel("C:\\Users\\S.Nivedhitham\\SNivedhitha\\PCP Analytics\\data\\New\\"+l[i]+".xlsx")
    df=clean(df)
    df,n=sync(df)
    df=pump_on_or_off(df)
    df=n_days_since_start(df)
    df=slope(n,df)
    df1=annotate_tubing_failure(df,n)
    return df1