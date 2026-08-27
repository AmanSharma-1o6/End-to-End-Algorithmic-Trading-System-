# End-to-End-Algorithmic-Trading-System-
##Backtester, Intraday Research, and Live Paper-Trading Engine

Built a Python backtester (pandas, yfinance) for MA/RSI strategies, enforcing lookahead-free signal lag.
Modeled per-side costs in bps & measured SPY break-even execution cost of 3.8-4 bps per side empirically.
Found VWAP edge on 1-min bars, gross Sharpe 9.88, ~10 bp per trade, net -2.71 Sharpe at 5 bps per side.
Deployed live paper trader on Alpaca API using limit orders, CSV audit trail, and paper/live safety gate.
Profiled latency: 0.82 s data fetch, 0.267 s order routing, 60 s cadence matched to edge decay timescale.

## Algorithmic Trading Strategy Backtester
<img width="1916" height="832" alt="UI" src="https://github.com/user-attachments/assets/f4a468b3-95c8-4aba-8cd9-97e2ee72b220" />
<img width="1917" height="906" alt="UI_2" src="https://github.com/user-attachments/assets/1bd14ec3-2815-4a96-ac6f-a609c0b8d3cb" />

## Live Trading — VWAP Mean Reversion (SPY)
<img width="1918" height="879" alt="LIve_trading" src="https://github.com/user-attachments/assets/c5a0eff7-02ea-4ce8-825d-0bad445168d7" />

## Project Report
<img width="940" height="374" alt="image" src="https://github.com/user-attachments/assets/b3944115-1d75-4d07-9bbc-f6322aa12f2b" />
<img width="931" height="379" alt="image" src="https://github.com/user-attachments/assets/cd7e0d23-f0da-4417-850e-1019381a0105" />
<img width="943" height="461" alt="image" src="https://github.com/user-attachments/assets/78d59ae4-08d8-4a46-b314-3ede92de489e" />
<img width="941" height="232" alt="image" src="https://github.com/user-attachments/assets/d335b8e7-2412-436b-961c-1e1bd901d9c5" />
<img width="942" height="623" alt="image" src="https://github.com/user-attachments/assets/583d672e-7feb-4621-bfa7-e7d3037debe7" />
<img width="944" height="804" alt="image" src="https://github.com/user-attachments/assets/4108a55a-8837-4a76-9ec2-c53fd886931a" />
<img width="943" height="219" alt="image" src="https://github.com/user-attachments/assets/d6a0b185-a84a-45df-b103-543be5181d19" />
<img width="945" height="466" alt="image" src="https://github.com/user-attachments/assets/840b7f1f-dce8-4d9e-be64-9c2b6206a357" />
<img width="942" height="483" alt="image" src="https://github.com/user-attachments/assets/a1c42202-8897-45a0-afd8-ecce8bb25473" />
<img width="942" height="439" alt="image" src="https://github.com/user-attachments/assets/614c3572-5e9d-4a2a-a4a3-4e48520304e0" />
<img width="943" height="468" alt="image" src="https://github.com/user-attachments/assets/d6f5229e-39a1-40bf-aed0-d3c7c444eb43" />
<img width="942" height="708" alt="image" src="https://github.com/user-attachments/assets/02e61a70-2ce6-43a9-8cd5-e142745e732a" />
<img width="941" height="828" alt="image" src="https://github.com/user-attachments/assets/b76ef7a6-f106-46b8-a0ee-94baed45b470" />
<img width="939" height="413" alt="image" src="https://github.com/user-attachments/assets/812df017-0810-48e3-9d19-16b5adbff2e3" />
<img width="939" height="535" alt="image" src="https://github.com/user-attachments/assets/9db7964d-2bdd-4ef7-9144-01b42065ef07" />
