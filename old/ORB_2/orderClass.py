from alice_blue import *

class place_order :
    def __init__(self, alice):
        self.alice = alice
    
    def placeBracketOrder(self,symbol,exchange,qty,sl,target,limitp,trans_type):
        symbolInfo = self.alice.get_instrument_by_symbol(exchange, symbol)
        response = self.alice.place_order(transaction_type = trans_type,
                     instrument = symbolInfo,
                     quantity = qty,
                     order_type = OrderType.Limit,
                     product_type = ProductType.BracketOrder,
                     price = limitp,
                     trigger_price = None,
                     stop_loss = sl,
                     square_off = target,
                     trailing_sl = None,
                     is_amo = False)
        return response