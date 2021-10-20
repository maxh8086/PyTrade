from nsepython import *
import pandas as pd


#  Functions that return d_1, d_2 and call and put prices
def d(sigma, S, K, r, t):
    d1 = 1 / (sigma * np.sqrt(t)) * ( np.log(S/K) + (r + sigma**2/2) * t)
    d2 = d1 - sigma * np.sqrt(t)
    return d1, d2

def call_price(sigma, S, K, r, t, d1, d2):
    C = norm.cdf(d1) * S - norm.cdf(d2) * K * np.exp(-r * t)
    return C

def put_price(sigma, S, K, r, t, d1, d2):
    P = -norm.cdf(-d1) * S + norm.cdf(-d2) * K * np.exp(-r * t)
    return P


#  Functions for Deltam Gamma, and  Theta
def delta(d_1, contract_type) :
    if contract_type == 'c' :
        return norm.cdf(d1)
    if contract_type == 'p' :
        return -norm.cdf(-d_1)


def gamma(d2, S, K, sigma, r, t) :
    return (K * np.exp(-r * t) * (norm.pdf(d2) / (S ** 2 * sigma * np.sqrt(t))))


def theta(d1, d2, S, K, sigma, r, t, contract_type) :
    if contract_type == 'c' :
        theta = -S * sigma * norm.pdf(d1) / (2 * np.sqrt(t)) - r * K * np.exp(-r * t) * norm.cdf(d2)
    if contract_type == 'p' :
        theta = -S * sigma * norm.pdf(-d1) / (2 * np.sqrt(t)) + r * K * np.exp(-r * t) * norm.cdf(-d2)

    return theta


def vega(sigma, S, K, r, t) :
    d1, d2 = d(sigma, S, K, r, t)
    v = S * norm.pdf(d1) * np.sqrt(t)
    return v

#  Using TSLA data from 5/9/2020 closing values
S = 819.42; print('S = ', S)
K = 1020; print('K = ', K)
r = 0.01; print('r = ', r)
t = 42 / 365; print('t = ', t)
sigma = 0.6966; print('sigma = ', sigma)


d1, d2 = d(sigma, S, K, r, t)
delta_call = delta(d1, 'c')
delta_put = delta(d1, 'p')
print('Call Delta = ', delta_call)
print('Put Delta = ', delta_put)
print( 'Gamma = ', gamma(d2, S, K, sigma, r, t) )

#####  Calculate Theta
print(S, K, r, t, sigma, d1, d2)
print( theta(d1, d2, S, K, sigma, r, t, 'c') )

print( 'Call Theta = ', theta(d1, d2, S, K, sigma, r, t, 'c') / 365 * 100)
print( 'Put Thata = ', theta(d1, d2, S, K, sigma, r, t, 'p') / 365 * 100)
print( vega(sigma, S, K, r, t) /100 )

