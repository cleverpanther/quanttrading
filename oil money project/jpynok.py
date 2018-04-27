# coding: utf-8
# In[67]:

#i call it oil money
#cuz its a statistical arbitrage on oil price and currency pair
#the inspiration came from an article i read last week
#it suggested to trade on forex of oil producing countries
#as the oil price went uprising
#what i intend to do is to build up a model
#we do a regression on historical datasets
#we use linear regression to do the prediction
#we set up thresholds based on the standard deviation of residual
#i take one deviation above as the upper threshold
#if the currency price breaches the upper threshold
#i take a short position as it is assumed to revert to its normal price range
#for the lower threshold, vice versa
#however, our regression is based on statistics
#we still need to consider fundamental influence
#what if the market condition has changed
#in that case our model wont work any more
#the price would deviate two sigmas away from predicted value
#which we should revert our positions
#e.g. the price is two sigmas above our predicted value
#we change our short to long as the market has changed
#there is probably hidden information in the uprising price
#lets follow the trend and see how it goes

#this idea sounds very silly
#nobody actually does it
#i just wanna see if this project is plausible
#perhaps im gonna suffer a huge loss from it
#first, we choose my currency norwegian krone
#norway is one of the largest oil producing countries with floating fx regime
#other oil producing countries such as saudi, iran, qatar have their fx pegged to usd
#russia is supposed to be a good training set
#however, russia got sanctioned by uncle sam a lot
#i tried jpyrub and the model barely captured anything
#every model seemed to be overfitted and had no prediction power
#i have uploaded russian ruble raw data in this folder for those who are willing to try

#after targetting at norwegian krone, we have to choose our base currency
#i took a look at norway's biggest trading partners to determine our variables
#i decided to include us dollar, euro and uk sterling as well as brent crude price
#i chose japanese yen as base currency
#cuz it doesnt have much correlation with nok
#lets get started!

import matplotlib.pyplot as plt
import statsmodels.api as sm
import pandas as pd
import numpy as np
import os
os.chdir('h:/')
os.getcwd()


# In[68]:
#this part is just data etl
#i got my raw data from eikon 4 
#so i gotta consolidate em before regression
#i have uploaded integrated dataset called raw.csv in this folder
#u can use pd.read_csv to replace this section
nok=pd.read_csv('nok.csv')
usd=pd.read_csv('usd.csv')
gbp=pd.read_csv('gbp.csv')
eur=pd.read_csv('eur.csv')
brent=pd.read_csv('brent.csv')
# In[69]:
#this loop is unnecessary
#i am just being lazy
#lets turn these prices into time series
for i in nok,usd,gbp,eur,brent:
    i.set_index(pd.to_datetime(i['Date']),inplace=True)
temp=pd.concat([nok['Last'],usd['Open'],eur['Last'],gbp['Last']],axis=1)
temp.columns=['nok','usd','eur','gbp']
temp['Date']=temp.index
crude=pd.DataFrame()
crude['brent']=brent['Last']
crude['Date']=brent.index
df=pd.merge(temp,crude)
df.set_index(pd.to_datetime(df['Date']),inplace=True)
del df['Date']
df.to_csv('raw.csv')



# In[70]:
#now we do our linear regression
#our historical data dated from 2013-4-25 to 2017-4-25
#we use data from 2017-4-25 to 2018-4-25 to do backtesting
x0=pd.concat([df['usd'],df['gbp'],df['eur'],df['brent']],axis=1)
x1=sm.add_constant(x0)
x=x1[x1.index<'2017-04-25']
y=df['nok'][df.index<'2017-04-25']
model=sm.OLS(y,x).fit()
print(model.summary(),'\n')
#nevertheless, from the summary u can tell there is multicollinearity
#to solve the problem, i used elastic net regression to achieve the convergence
#plz check the following codes

#from sklearn.linear_model import ElasticNetCV as en 
#m=en(alphas=[0.0001, 0.0005, 0.001, 0.01, 0.1, 1, 10], \
#l1_ratio=[.01, .1, .5, .9, .99],  max_iter=5000).fit(x0[x0.index<'2017-04-25'], y)  
#print(m.intercept_,m.coef_)

#results:
#0.0865891404588 [  0.00000000e+00   0.00000000e+00   0.00000000e+00  -2.50754626e-06]
#so brent crude can be decomposed into jpyusd,jpyeur,jpygbp
#us dollar possibly can account for some oil price change
#what about japanese yen, euro, uk sterling
#none of these countries are major oil producers
#it simply doesnt make sense
#even though a simple correlation between norwegian krone and brent crude is what i desired
#it doesnt work this way
#i used the fitted value to compare with actual value 
#the error term is extremely large 
#basically i cant use the model to do any statistical arbitrage
#unfortunately i have to live with this model
#as it has some prediction power over the next several months


# In[72]:
#lets generate signals
#we set one sigma of the residual as thresholds
#two sigmas of the residual as stop orders
upper=np.std(model.resid)
lower=-upper
signals=df[df.index>='2017-04-25']
signals['fitted']=signals['usd']*model.params[1]+signals['gbp']*model.params[2]+signals['eur']*model.params[3]+signals['brent']*model.params[4]+model.params[0]
signals['upper']=signals['fitted']+0.5*upper
signals['lower']=signals['fitted']+0.5*lower
signals['stop profit']=signals['fitted']+2*upper
signals['stop loss']=signals['fitted']+2*lower
signals['signals']=0



# In[83]:
#while doing a traversal
#we apply the rules i mentioned before
#if actual price goes beyond upper threshold
#we take a short and bet on its reversion process
#vice versa
#we use cumsum to make sure our signals only get generated
#for the first time condions are met
#when actual price hit the stop order boundary
#we revert our positions
for j in signals.index:
    if pd.Series(signals['nok'])[j]>pd.Series(signals['upper'])[j]:
        signals['signals'][j:j]=-1  
          
    if pd.Series(signals['nok'])[j]<pd.Series(signals['lower'])[j]:
        signals['signals'][j:j]=1 
       
    signals['cumsum']=signals['signals'].cumsum()

    if pd.Series(signals['cumsum'])[j]>1 or pd.Series(signals['cumsum'])[j]<-1:
        signals['signals'][j:j]=0
  
    if pd.Series(signals['nok'])[j]>pd.Series(signals['stop profit'])[j]:         
        signals['cumsum']=signals['signals'].cumsum()
        signals['signals'][j:j]=-signals['cumsum'][j:j]+1
        signals['cumsum']=signals['signals'].cumsum()
        break

    if pd.Series(signals['nok'])[j]<pd.Series(signals['stop loss'])[j]:
        signals['cumsum']=signals['signals'].cumsum()
        signals['signals'][j:j]=-signals['cumsum'][j:j]-1
        signals['cumsum']=signals['signals'].cumsum()
        break

        
# In[84]:
#next, we plot the usual positions as the first figure
fig=plt.figure()
ax=fig.add_subplot(111)
signals['nok'].plot(label='jpynok')
ax.plot(signals.loc[signals['signals']>0].index,signals['nok'][signals['signals']>0],lw=0,marker='^',c='g',label='long')
ax.plot(signals.loc[signals['signals']<0].index,signals['nok'][signals['signals']<0],lw=0,marker='v',c='r',label='short')
plt.legend()
plt.title('jpynok positions')
plt.ylabel('jpynok')
plt.show()


# In[85]:
#the second figure explores thresholds and boundaries for signal generation
#we can see after 2017/10/28, jpynok price went skyrocketing
#as a data scientist, we may ask why?
#is it a problem of our model identification
#or the fundamental situation of jpynok or oil price changed
signals['fitted'].plot()
signals['nok'].plot()
signals['upper'].plot(linestyle='--')
signals['lower'].plot(linestyle='--')
signals['stop profit'].plot(linestyle=':')
signals['stop loss'].plot(linestyle=':')
plt.legend(loc='best')
plt.title('fitted vs actual')
plt.ylabel('jpynok')
plt.show()

#if we decompose jpynok into long term trend and short term random process
#we could clearly see that brent crude has dominated short term random process
#so what changed the long term trend?
#there are a few options as reasons
#saudi and iran endorsed an extension of production caps on that particular date
#donald trump got elected as potus so he would lift the ban on domestics shale oil restriction
(signals['brent'][signals['stop profit']<signals['nok']]).plot(c='#FFA07A')
plt.legend(loc='best')
plt.title('brent crude after 2017/10/28')
plt.ylabel('brent future contract in jpy')
plt.show()


# In[96]:
#then lets do a pnl analysis
capital0=5000
positions=10000
portfolio=pd.DataFrame(index=signals.index)
portfolio['holding']=signals['nok']*signals['cumsum']*positions
portfolio['cash']=capital0-(signals['nok']*signals['signals']*positions).cumsum()
portfolio['total asset']=portfolio['holding']+portfolio['cash']
portfolio['signals']=signals['signals']

# In[98]:
#we plot how our asset value changes over time
fig=plt.figure()
ax=fig.add_subplot(111)
portfolio['total asset'].plot()
ax.plot(portfolio.loc[portfolio['signals']>0].index,portfolio['total asset'][portfolio['signals']>0],lw=0,marker='^',c='g',label='long')
ax.plot(portfolio.loc[portfolio['signals']<0].index,portfolio['total asset'][portfolio['signals']<0],lw=0,marker='v',c='r',label='short')
plt.legend()
plt.title('portfolio performance')
plt.ylabel('asset value')
plt.show()
