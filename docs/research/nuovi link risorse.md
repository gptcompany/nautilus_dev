https://www.tradingview.com/u/LuxAlgo/#published-scripts
283 scripts da analizzare per luxalgo
https://www.tradingview.com/script/JRqryeJ5-Liquidity-Sweeps-LuxAlgo/
https://www.tradingview.com/script/ZxHyWlMd-Liquidity-Grabs-Flux-Charts/
https://www.tradingview.com/script/7dNQa9Ig-Liquidity-Sniper-V3-ANTI-FAKEOUT/
https://www.tradingview.com/script/HvOAnchA-Cumulative-Volume-Delta-Divergence-TradingFinder-Periodic-EMA/
topic molto importante
https://www.tradingview.com/script/3DTOFolH-Volume-HeatMap-Divergence-BigBeluga/
topic molto importante per riconoscere zone
https://www.tradingview.com/script/ihy9IpZi-Tape-Speed-Pulse-Pace-Direction-v6-Climax/
atlas speed of tape
pace of tape
smart tape


codice ninja trader per speed of tape da verificare/improve:
"""
Calculate    = Calculate.OnEachTick;

protected override void OnBarUpdate()
        {
            int pace = 0;
            int i = 0;
            while(i < CurrentBar)
            {
                TimeSpan ts = Time[0] - Time[i];
                if (ts.TotalSeconds < period)
                    pace += Bars.BarsPeriod.Value;                    

                else     break;   ++i;    
            }
"""


buona risorsa: https://intelligenttradingtech.blogspot.com/2011/03/can-one-beat-random-walk-impossible-you.html