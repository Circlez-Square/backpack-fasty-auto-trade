from bpx.bpx import *
from bpx.bpx_pub import *
import time
from dotenv import load_dotenv
import os

if __name__ == '__main__':
    # 加载当前目录的 .env 文件
    load_dotenv()
    run_pair = 'SOL'
    pair_name ='SOL_USDC'
    pair_accuracy=2 #交易对价格精度
    # 读取环境变量
    api_secret = os.getenv('API_SECRET')
    api_key = os.getenv('API_KEY')
    wish_vol =int(os.getenv('WISH_VOLUME'))
    bpx = BpxClient()
    bpx.init(        
        api_key=api_key,
        api_secret=api_secret,
    )
    wish_vol=wish_vol #期望刷的量，单位USDC
    def buy_and_sell(usdc_available,sol_available,asks_price,bids_price):
        get_diff_price = round(asks_price-bids_price,pair_accuracy)
        if get_diff_price == 1/int(10**pair_accuracy):   #掛單簿沒有滑價時 差0.01的價差 當maker = 千分之8.5  大家對價格有共識 ，但最好能檢查成交量
            if usdc_available>5:

                bpx.ExeOrder(
                    symbol=pair_name, 
                    side='Bid', 
                    orderType='Limit', 
                    timeInForce='', 
                    quantity=int(usdc_available/bids_price*100)/100, 
                    price=bids_price,
                    )
                print(f'try buy {usdc_available} USDC at {bids_price}')
                return usdc_available
            elif sol_available>1/int(10**pair_accuracy):
                bpx.ExeOrder(
                    symbol=pair_name, 
                    side='Ask', 
                    orderType='Limit', 
                    timeInForce='', 
                    quantity=sol_available, 
                    price=asks_price,
                    )      
                print(f'try sell {sol_available} {run_pair} at {asks_price}')    
                return sol_available* asks_price
        else:
            if usdc_available>5:
                bids_price = bids_price+1/int(10**pair_accuracy)

                bpx.ExeOrder(
                    symbol=pair_name, 
                    side='Bid', 
                    orderType='Limit', 
                    timeInForce='', 
                    quantity=int(usdc_available/bids_price*100)/100,  
                    price=round(bids_price,2),
                    )

                print(f'try buy {usdc_available} USDC at {bids_price}')
                return usdc_available
            elif sol_available>1/int(10**pair_accuracy):
                asks_price=asks_price-1/int(10**pair_accuracy)

                bpx.ExeOrder(
                    symbol=pair_name, 
                    side='Ask', 
                    orderType='Limit', 
                    timeInForce='', 
                    quantity=sol_available, 
                    price=round(asks_price,2),
                    )
           
                print(f'try sell {sol_available} {run_pair} at {asks_price}')  
                return sol_available* asks_price
    def tarde_once_logical():
        start_time = time.time()
        sol_market_depth1 =Depth(pair_name)
        sol_market_depth2 =Depth(pair_name)
        end_time = time.time()
        elapsed_time = end_time - start_time

        # print(account_balance)
        asks_depth1 = round(float(sol_market_depth1['asks'][0][1]),2)
        asks_price1 = round(float(sol_market_depth2['asks'][0][0]), pair_accuracy)
        bids_depth1 = round(float(sol_market_depth1['bids'][-1][1]),2)
        bids_price1 = round(float(sol_market_depth2['bids'][-1][0]), pair_accuracy)
        # print(asks_depth1,bids_depth1)
        asks_depth2 = round(float(sol_market_depth2['asks'][0][1]),2)
        asks_price2 = round(float(sol_market_depth2['asks'][0][0]),pair_accuracy)
        bids_depth2 = round(float(sol_market_depth2['bids'][-1][1]),2)
        bids_price2=round(float(sol_market_depth2['bids'][-1][0]),pair_accuracy)
        # print(asks_depth2,bids_depth2)
        ask_quick_market=0
        bid_quick_market=-1
        if asks_price1 == asks_price2:
            if (asks_depth1-asks_depth2)/elapsed_time*5>asks_depth2:
                ask_quick_market+=1
        if bids_price1 == bids_price2:         
            if (bids_depth1-bids_depth2)/elapsed_time*5>bids_depth2:
                bid_quick_market-=1
        # print(f"The time difference is {elapsed_time} seconds")

        asks_price=round(float(sol_market_depth2['asks'][ask_quick_market][0]),pair_accuracy)
        bids_price=round(float(sol_market_depth2['bids'][bid_quick_market][0]),pair_accuracy)
        try:
            vol = buy_and_sell(usdc_available,sol_available,asks_price,bids_price)
        except:
            vol = 0
            print('发送交易时发生错误')
        return vol

    begin_vol = int(wish_vol)
    run_time=time.time()
    account_balance=bpx.balances()
    # 获取余额
    try:
        begin_usdc_available = float(account_balance['USDC']['available'])
    except:
        begin_usdc_available = 0
    
    try:
        begin_sol_available = float(account_balance[run_pair]['available'])
    except:
        begin_sol_available = 0
    if begin_usdc_available<5 and begin_usdc_available<0.02:
        bpx.ordersCancel(pair_name)
        account_balance=bpx.balances()
        # 获取余额
        begin_usdc_available = int(float(account_balance['USDC']['available'])*100)/100
        begin_sol_available = int(float(account_balance[run_pair]['available'])*100)/100    
    print(f'初始USDC余额：{begin_usdc_available} USDC')
    print(f'初始{run_pair}余额：{begin_sol_available} {run_pair}')

    while wish_vol>0:
        account_balance=bpx.balances()
        # 获取余额
        usdc_available = int(float(account_balance['USDC']['available'])*100)/100
        try:
            sol_available = int(float(account_balance[run_pair]['available'])*100)/100
        except:
            sol_available=0
        print(f'当前USDC余额：{usdc_available} USDC')
        print(f'当前{run_pair}余额：{sol_available} {run_pair}')
        if usdc_available<5 and sol_available<0.02:
            order = bpx.ordersQuery(pair_name)
            now_time =time.time()
            if order and now_time-run_time >5:
                bpx.ordersCancel(pair_name)
                unfinish_vol=0
                for each_order in order:
                    unfinish_vol += (float(each_order['quantity']) - float(each_order['executedQuoteQuantity'])) *float(each_order['price'] )
                wish_vol +=unfinish_vol
                print(f'取消未成交订单 {unfinish_vol} USDC')
            continue    
        run_time = time.time()
        vol = tarde_once_logical()
        wish_vol -=vol
    
    order = bpx.ordersQuery(pair_name)
    bpx.ordersCancel(pair_name)
    unfinish_vol=0
    for each_order in order:
        unfinish_vol += (float(each_order['executedQuoteQuantity'])) *float(each_order['price'] )
    wish_vol +=unfinish_vol
    print(f'刷量结束，共刷{begin_vol - wish_vol} USDC')
    account_balance=bpx.balances()
    # 获取余额
    final_usdc_available = float(account_balance['USDC']['available'])
    final_sol_available = float(account_balance[run_pair]['available'])
    print(f'最终USDC余额：{final_usdc_available} USDC')
    print(f'最终{run_pair}余额：{final_sol_available} {run_pair}')
    final_depth = Depth(pair_name)
    price =  round(float(final_depth['bids'][-1][0]),pair_accuracy)
    wear = round(price*(begin_sol_available-final_sol_available) + begin_usdc_available-final_usdc_available,6)
    wear_ratio = round(wear/(begin_vol - wish_vol),6)
    print(f'本次刷量磨损 {wear} USDC, 磨损率 {wear_ratio}')
