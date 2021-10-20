import mibian
#  Using TSLA data from 5/9/2020 closing values
underlyingPrice = 14755;
strikes = 14850, 14800;
interestRate = 10;
daysToExpiration = 1;
volatility = 25.06;
gamma = vega = theta_ce = delta_ce = estimate_ce = strikePrice = theta_pe = delta_pe = estimate_pe = []
for strike in strikes:
    # BS([underlyingPrice, strikePrice, interestRate, daysToExpiration], volatility=x, callPrice=y, putPrice=z)
    c = mibian.BS([underlyingPrice, strike, interestRate, daysToExpiration], volatility=volatility)
    gamma.append(round(c.gamma,4))
    vega.append(round(c.vega, 4))
    theta_ce.append(round(c.callTheta,2))
    delta_ce.append(round(c.callDelta,2))
    estimate_ce.append(round(c.callPrice,2))
    strikePrice.append(strike)
    estimate_pe.append(round(c.putPrice,2))
    delta_pe.append(round(c.putDelta,2))
    theta_pe.append(round(c.putTheta,2))

df = { 'gamma_ce' : gamma,
       'vega_ce': vega,
       'theta_ce': theta_ce,
       'delta_ce': delta_ce,
       'estimate_ce': estimate_ce,
       'strikePrice': strikePrice,
       'estimate_pe': estimate_pe,
       'delta_pe': delta_pe,
       'theta_pe': theta_pe,
       'vega_pe': vega,
       'gamma_pe': gamma
       }

print(df)
# print('Call Price', round(c.callPrice,2))
# print('Call Delta', round(c.callDelta,2))
# print('Call Theta', round(c.callTheta,2))
# print('Call vega', round(c.vega,4))
# print('Call gamma', round(c.gamma,4))
# #put result
# print('Put Price', round(c.putPrice,2))
# print('Put Delta', round(c.putDelta,2))
# print('Put Theta', round(c.putTheta,2))