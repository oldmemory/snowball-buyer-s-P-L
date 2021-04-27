# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 10:45:46 2021

@author: these
"""
basedir=r'D:\西南证券\衍生品\定价\雪球\程序'
import numpy as np
import pandas as pd
import os
os.chdir(basedir)
from pre_param import *
import datetime
from dateutil.relativedelta import relativedelta
#from WindPy import w
#w.start()
#w.menu()
#hist_close=w.wsd("000905.SH", "close", "2015-09-09", "2021-04-14", "")
#hist_close=pd.DataFrame([hist_close.Times,hist_close.Data[0]]).T
#hist_close.to_excel('000905History.xlsx')
hist_close=pd.read_excel('000905History.xlsx',index_col=0)
hist_close['price']
#2015-9-14到2021-4-14
#每个观察日
#trd_day=w.tdays("2015-09-14","2024-04-14")
#trd_week=w.tdays("2015-09-14","2021-04-14","Period=W")#周最后一天
#trd_month=w.tdays("2015-09-14","2021-04-14","Period=M")#月最后一天
#trd_day=trd_day.Times
#trd_week=trd_week.Times
#trd_month=trd_month.Times
#pd.DataFrame(trd_day).to_excel(r'.\持有分析\trd_day.xlsx')
#pd.DataFrame(trd_week[:-1]).to_excel(r'.\持有分析\trd_week.xlsx')
#pd.DataFrame(trd_month[:-1]).to_excel(r'.\持有分析\trd_month.xlsx')
trd_day=pd.read_excel(r'.\持有分析\trd_day.xlsx',index_col=0)#最多到2022-12-30
today=datetime.datetime.strptime('2021-04-14','%Y-%m-%d')
trd_day_tillnow=trd_day[trd_day[0]<=today]
trd_week=pd.read_excel(r'.\持有分析\trd_week.xlsx',index_col=0)
trd_month=pd.read_excel(r'.\持有分析\trd_month.xlsx',index_col=0)
#################首先针对所有的日期，生成其对应的KO_dates和enddate
###目前都是3个月锁定，2年期限
no_sep_months=22
sep_months=[i+3 for i in range(no_sep_months)]
#####如果遇到非交易日则往后移
#all_dates=pd.DataFrame([],index=trd_day_tillnow[0],columns=[str(i) for i in range(no_sep_months)]+['enddate'])
#for i_row in range(all_dates.shape[0]):
#    startdate=all_dates.index[i_row]
#    temp=startdate+relativedelta(years=2)
#    while( ((temp in trd_day[0].tolist())==False) and (temp<=trd_day.iloc[-1,0])):
#        temp=temp+datetime.timedelta(days=1)
#    all_dates.loc[startdate,'enddate']=temp
#    
#    #temp_KO_dates=[]
#    for sep_month_index in range(no_sep_months):
#        sep_month=sep_months[sep_month_index]
#        temp=startdate+relativedelta(months=sep_month)
#        while ( ((temp in trd_day[0].tolist())==False) and (temp<=trd_day.iloc[-1,0])):
#            temp=temp+datetime.timedelta(days=1)
#        #temp_KO_dates.append(temp)
#        all_dates.loc[startdate,str(sep_month_index)]=temp
#all_dates.to_excel(r'.\持有分析\all_dates.xlsx')    
########################################
all_dates=pd.read_excel(r'.\持有分析\all_dates.xlsx',index_col=0)
#第一类：只有敲出票息
class simplified_snowball(object):
    def __init__(self,startdate,K=None,enddate=None,Notional=100,KO_ratio=1.03,KO_rebate=0,KO_dates=None,\
                 KI_ratio=0.75,KI_payoff=nothing_payoff,nothing_happens_payoff=0):
        self.KO_rebate=KO_rebate
        self.KI_payoff=KI_payoff
        self.nothing_happens_payoff=nothing_happens_payoff
        self.startdate=startdate
        if enddate:
            self.enddate=enddate
        else:
            self.enddate=all_dates.loc[startdate,'enddate']
        self.actual_KO_date=None
        self.actual_KI_date=None
        self.Notional=Notional
        if K:
            self.K=K
        else:
            self.K=hist_close.loc[startdate,'price']
        self.KO=self.K*KO_ratio
        self.KI=self.K*KI_ratio
        self.payoff=None
        self.expired=False
        self.expired_type=0#-1代表情况不明，0未完结，1代表敲出，2代表未敲出未敲入，3代表未敲出并且敲入
        if KO_dates:
            self.KO_dates=KO_dates
        else:
            KO_dates=[]
            for i in range(no_sep_months):
                KO_dates.append(all_dates.loc[startdate,str(i)])
            self.KO_dates=KO_dates
    def reset_KO(self,KO_ratio):
        self.KO_ratio=KO_ratio
        self.KO=self.K*KO_ratio
    def reset_KI(self,KI_ratio):
        self.KI_ratio=KI_ratio
        self.KI=self.K*KI_ratio

class typeI(simplified_snowball):
    def __init__(self,startdate,K=None,enddate=None,Notional=100,KO_ratio=1.03,KO_rebate=0.01,KO_dates=None):
        super(typeI,self).__init__(startdate=startdate,K=K,enddate=enddate,Notional=Notional,KO_ratio=KO_ratio,
             KO_rebate=KO_rebate,KO_dates=KO_dates,KI_ratio=0)
    
    def payoff_calc(self):
        if len(self.KO_dates)==0:return(None)
        effective_KO_dates=[i for i in self.KO_dates if i<=trd_day_tillnow.iloc[-1,0]]
        if len(effective_KO_dates)==0:return(None)
        underlying_price=hist_close.loc[effective_KO_dates,'price']
        KO_result=np.where(underlying_price>=self.KO)
        if len(KO_result[0]>0):
            self.actual_KO_date=effective_KO_dates[KO_result[0][0]]
            self.payoff=(self.actual_KO_date-self.startdate).days/naturalday_year*self.Notional*self.KO_rebate
            self.expired=True
            self.expired_type=1
        else:
            if self.enddate>trd_day_tillnow.iloc[-1,0]:
                pass
            else:
                self.actual_KO_date=None
                self.payoff=0
                self.expired=True
                self.expired_type=-1


class typeII(simplified_snowball):
    def __init__(self,startdate,K=None,enddate=None,Notional=100,KO_ratio=1.03,KO_rebate=0,KO_dates=None,KI_ratio=0.75,\
                 KI_payoff=nothing_payoff,nothing_happens_payoff=0.01):
        super(typeII,self).__init__(startdate=startdate,K=K,enddate=enddate,Notional=Notional,KO_ratio=KO_ratio,
             KO_rebate=KO_rebate,KO_dates=KO_dates,KI_ratio=KI_ratio,KI_payoff=KI_payoff,nothing_happens_payoff=nothing_happens_payoff)
    
    def payoff_calc(self):
        if len(self.KO_dates)==0:return(None)
        effective_KO_dates=[i for i in self.KO_dates if i<=trd_day_tillnow.iloc[-1,0]]
        if len(effective_KO_dates)==0:return(None)
        underlying_price=hist_close.loc[effective_KO_dates,'price']
        KO_result=np.where(underlying_price>=self.KO)
        if len(KO_result[0]>0):
            self.actual_KO_date=effective_KO_dates[KO_result[0][0]]
            self.payoff=(self.actual_KO_date-self.startdate).days/naturalday_year*self.Notional*self.KO_rebate
            self.expired=True
            self.expired_type=1
        elif self.enddate<=trd_day_tillnow.iloc[-1,0]:
            underlying_price=hist_close.loc[self.startdate:self.enddate,'price']
            if min(underlying_price)<=self.KI:
                self.actual_KI_date=underlying_price.index[np.where(underlying_price<=self.KI)[0][0]]
                self.payoff=self.KI_payoff(S=underlying_price[-1],K=self.K)*self.Notional
                self.expired=True
                self.expired_type=3
            else:
                self.actual_KI_date=None
                self.payoff=(self.enddate-self.startdate).days/naturalday_year*self.Notional*self.nothing_happens_payoff
                self.expired=True
                self.expired_type=2


class typeIII(simplified_snowball):
    def __init__(self,startdate,K=None,enddate=None,Notional=100,KO_ratio=1.03,KO_rebate=0,KO_dates=None,KI_ratio=0.75,\
                 KI_payoff=minus_vanilla_put_payoff,nothing_happens_payoff=0):
        super(typeIII,self).__init__(startdate=startdate,K=K,enddate=enddate,Notional=Notional,KO_ratio=KO_ratio,
             KO_rebate=KO_rebate,KO_dates=KO_dates,KI_ratio=KI_ratio,KI_payoff=KI_payoff,nothing_happens_payoff=nothing_happens_payoff)
    
    def payoff_calc(self):
        if len(self.KO_dates)==0:return(None)
        effective_KO_dates=[i for i in self.KO_dates if i<=trd_day_tillnow.iloc[-1,0]]
        if len(effective_KO_dates)==0:return(None)
        underlying_price=hist_close.loc[effective_KO_dates,'price']
        KO_result=np.where(underlying_price>=self.KO)
        if len(KO_result[0]>0):
            self.actual_KO_date=effective_KO_dates[KO_result[0][0]]
            self.payoff=(self.actual_KO_date-self.startdate).days/naturalday_year*self.Notional*self.KO_rebate
            self.expired=True
            self.expired_type=1
        elif self.enddate<=trd_day_tillnow.iloc[-1,0]:
            underlying_price=hist_close.loc[self.startdate:self.enddate,'price']
            if min(underlying_price)<=self.KI:
                self.actual_KI_date=underlying_price.index[np.where(underlying_price<=self.KI)[0][0]]
                self.payoff=self.KI_payoff(S=underlying_price[-1],K=self.K)*self.Notional
                self.expired=True
                self.expired_type=3
            else:
                self.actual_KI_date=None
                self.payoff=(self.enddate-self.startdate).days/naturalday_year*self.Notional*self.nothing_happens_payoff
                self.expired=True
                self.expired_type=2
##生成payoff
snowballs=[[],[],[]]#第一个序列是typeI,typeII,typeIII
for i_date in trd_day_tillnow[0]:
    temp_snowball_typeI=typeI(startdate=i_date,Notional=100,KO_rebate=0.01,KO_ratio=1.03)
    temp_snowball_typeI.payoff_calc()
    snowballs[0].append(temp_snowball_typeI)
    #temp_snowball_typeI.payoff
    temp_snowball_typeII=typeII(startdate=i_date,Notional=100,KO_ratio=1.03,KI_ratio=0.75,nothing_happens_payoff=0.01)
    temp_snowball_typeII.payoff_calc()
    snowballs[1].append(temp_snowball_typeII)
    temp_snowball_typeIII=typeIII(startdate=i_date,Notional=100,KO_ratio=1.03,KI_ratio=0.75,KI_payoff=minus_vanilla_put_payoff)
    temp_snowball_typeIII.payoff_calc()
    snowballs[2].append(temp_snowball_typeIII)

actual_over_dates=[]#敲出日或者到期日   
actual_over_types=[]
for i_date_index in range(trd_day_tillnow.shape[0]):
    temp=snowballs[0][i_date_index].actual_KO_date
    if temp:
        actual_over_dates.append(temp)
    else:
        actual_over_dates.append(snowballs[0][i_date_index].enddate)
    
    actual_over_types.append(snowballs[2][i_date_index].expired_type)
actual_over_dates=pd.DataFrame([actual_over_dates,trd_day_tillnow[0]],index=['overdate','startdate']).T
actual_over_dates=actual_over_dates.set_index('overdate')


actual_KI_dates=[]#敲出日或者到期日   
for i_date_index in range(trd_day_tillnow.shape[0]):
    temp=snowballs[0][i_date_index].actual_KO_date
    if temp:
        actual_over_dates.append(temp)
    else:
        actual_over_dates.append(snowballs[0][i_date_index].enddate)
    
    actual_over_types.append(snowballs[2][i_date_index].expired_type)
actual_over_dates=pd.DataFrame([actual_over_dates,trd_day_tillnow[0]],index=['overdate','startdate']).T
actual_over_dates=actual_over_dates.set_index('overdate')

#temp=actual_over_dates.loc[datetime.datetime.strptime('2017-12-11','%Y-%m-%d')]

#############首先构建购买雪球的策略和头寸
###每周购买固定规模的
###可分为投入、占资、兑付时间序列
##每周购买
Mul_Notional=100
Mul_KO_rebate=0.2/0.01
Mul_nothing_happens_payoff=0.2/0.01
input_week=[[],[],[]]#第一个序列是typeI,typeII,typeIII
occupying_week=[[0],[0],[0]]#occupying_week比另外两个多一个初期为0的数据，便于加总
payoff_week=[[],[],[]]
interest_week=[[],[],[]]
trd_week=pd.read_excel(r'.\持有分析\trd_week.xlsx',index_col=0)
temp_trd_week=pd.read_excel(r'.\持有分析\trd_week.xlsx',index_col=0)

for i_row in range(trd_day_tillnow.shape[0]):
    for j_row in range(3):
        input_week[j_row].append(0)
        occupying_week[j_row].append(occupying_week[j_row][i_row])  
        payoff_week[j_row].append(0)    
        interest_week[j_row].append(0)  
    #处理当日敲出或者到期    
    temp=np.array([])
    if trd_day_tillnow.iloc[i_row,0] in actual_over_dates.index:
        temp=actual_over_dates.loc[[ trd_day_tillnow.iloc[i_row,0] ]]##选取结束日期为当前日期的
    kept_row=[]##选取其中是真正用每周购买策略买过的
    if temp.shape[0]>0:
        for j_row in range(temp.shape[0]):
            if temp.iloc[j_row,0] in trd_week[0].tolist():
                kept_row.append(j_row)
        temp=temp.iloc[kept_row,:]
    if temp.shape[0]>0:
        for j_row in range(temp.shape[0]):
            temp_index=np.where(trd_day_tillnow[0]==temp.iloc[j_row,0])[0]
            if len(temp_index)>1:print(i_row)
            temp_index=temp_index[0]
            
            payoff_week[0][i_row]=payoff_week[0][i_row]+Mul_Notional+\
            Mul_Notional*Mul_KO_rebate*snowballs[0][temp_index].payoff/snowballs[0][temp_index].Notional
            interest_week[0][i_row]=interest_week[0][i_row]+\
            Mul_Notional*Mul_KO_rebate*snowballs[0][temp_index].payoff/snowballs[0][temp_index].Notional
            occupying_week[0][i_row+1]=occupying_week[0][i_row+1]-Mul_Notional
            
            payoff_week[1][i_row]=payoff_week[1][i_row]+Mul_Notional+\
            Mul_Notional*Mul_nothing_happens_payoff*snowballs[1][temp_index].payoff/snowballs[1][temp_index].Notional
            interest_week[1][i_row]=interest_week[1][i_row]+\
            Mul_Notional*Mul_nothing_happens_payoff*snowballs[1][temp_index].payoff/snowballs[1][temp_index].Notional
            occupying_week[1][i_row+1]=occupying_week[1][i_row+1]-Mul_Notional
                        
            payoff_week[2][i_row]=payoff_week[2][i_row]+Mul_Notional+\
            Mul_Notional*snowballs[2][temp_index].payoff/snowballs[2][temp_index].Notional
            interest_week[2][i_row]=interest_week[2][i_row]+\
            Mul_Notional*snowballs[2][temp_index].payoff/snowballs[2][temp_index].Notional
            occupying_week[2][i_row+1]=occupying_week[2][i_row+1]-Mul_Notional
    #处理当日新增认购        
    if (temp_trd_week.shape[0]>0) and (trd_day_tillnow.iloc[i_row,0]==temp_trd_week.iloc[0,0]):
        input_week[0][i_row]=input_week[0][i_row]+Mul_Notional
        occupying_week[0][i_row+1]=occupying_week[0][i_row+1]+Mul_Notional
        input_week[1][i_row]=input_week[1][i_row]+Mul_Notional
        occupying_week[1][i_row+1]=occupying_week[1][i_row+1]+Mul_Notional
        input_week[2][i_row]=input_week[2][i_row]+Mul_Notional
        occupying_week[2][i_row+1]=occupying_week[2][i_row+1]+Mul_Notional
        
        temp_trd_week.drop(index=temp_trd_week.index[0],inplace=True)
    


existing_month=[]
expired_month=[]



###############然后开始每日观察
for i in range(len(hist_close.shape[0])):
    




KI_ratio=0.75


Bonus=0.01
KI_payoff=vanilla_put
