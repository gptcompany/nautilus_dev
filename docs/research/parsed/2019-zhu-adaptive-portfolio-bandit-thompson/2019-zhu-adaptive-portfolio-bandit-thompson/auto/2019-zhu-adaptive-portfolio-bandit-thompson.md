# Adaptive Portfolio by Solving Multi-armed Bandit via Thompson Sampling

Mengying $\mathbf { Z } \mathbf { h } \mathbf { u } ^ { 1 }$ , Xiaolin Zheng1∗ , Yan Wang2 and Yuyuan $\mathbf { L i } ^ { 1 }$ and Qianqiao Liang1

1Department of Computer Science, Zhejiang University, Hangzhou, China 2Macqaurie University, Department of Computing, Sydney, NSW, Australia {mengyingzhu,xlzheng,11821022,liangqq} $@$ zju.edu.cn, yan.wang $@$ mq.edu.au

# Abstract

As the cornerstone of modern portfolio theory, Markowitz’s mean-variance optimization is considered a major model adopted in portfolio management. However, due to the difficulty of estimating its parameters, it cannot be applied to all periods. In some cases, naive strategies such as Equallyweighted and Value-weighted portfolios can even get better performance. Under these circumstances, we can use multiple classic strategies as multiple strategic arms in multi-armed bandit to naturally establish a connection with the portfolio selection problem. This can also help to maximize the rewards in the bandit algorithm by the trade-off between exploration and exploitation. In this paper, we present a portfolio bandit strategy through Thompson sampling which aims to make online portfolio choices by effectively exploiting the performances among multiple arms. Also, by constructing multiple strategic arms, we can obtain the optimal investment portfolio to adapt different investment periods. Moreover, we devise a novel reward function based on users’ different investment risk preferences, which can be adaptive to various investment styles. Our experimental results demonstrate that our proposed portfolio strategy has marked superiority across representative realworld market datasets in terms of extensive evaluation criteria.

# 1 Introduction

The portfolio selection problem is a fundamental issue in the financial sector for many asset investments, including funds, stocks, bonds, and options. According to Gary Brinson, the father of global asset allocation, “Asset allocation is the main factor that affects all overall returns.” In the long run, more than $90 \%$ of a portfolio’s performance is attributable to its asset allocation [Brinson et al., 1995]. Thus, asset allocation of a portfolio is the key determinant of performance, risk, and volatility over time.

Modern portfolio theory and analysis tend to build upon the seminal work of Markowitz [Markowitz, 1952]. Up to now, the mean-variance paradigm has remained the mainstream choice for academia and industry. However, the main problem of using a single strategy is that it cannot be adapted to the changing environment. For instance, in an event of the stock market crash, the sold-all strategy with cash will have a good performance. Meanwhile, during the bull market, the buy-and-hold strategy is likely to perform even better. In terms of this issue, a simple approach in the investment field is to periodically review the effectiveness of the current strategy and appropriately adjust the strategy for the next phase. This is a typical problem of exploration and exploitation. Therefore, we use reinforcement learning to solve the problem of how to determine optimal portfolio strategy to adapt for different investment periods.

Meanwhile, each investor’s pursuit of risk and benefit is different, which is called the user’s investment risk preference. Although a good strategy can ultimately help in achieving a good return, not every investor is willing to take on some risks in the process. For example, users with a low risk tolerance are unlikely to consider short-term losses, whereas users with high risk tolerance tend to pursue high returns and usually do not care about retracement. For this reason, we take the users’ investment risk preferences into account and propose a novel reward function, which can be adaptive to various investment styles such as high-risk-high-return and lowrisk-low-return investment style.

In this paper, we first turn the portfolio problem into a multi-armed bandit problem and construct a series of strategic arms basing on the classic strategies. Subsequently, we apply Thompson sampling method to select strategic arm and further update the Beta distribution of strategic arms based on the user’s investment risk preference. The contributions of the present work are summarized as follows:

• To adapt to different market conditions in different periods, we utilize the multi-armed bandit problem to adaptively select the most suitable strategy to form an online portfolio strategy.   
• We devise a novel reward function based on the users’ investment risk preferences to ascertain that the method fits a variety of users’ needs. This helps to achieve different return-to-risk ratio.

• Experimental results indicate that the proposed portfolio strategy has marked superiority across representative real-world market datasets in terms of a series of standard financial evaluation indicators, which include Sharpe ratios, cumulative wealth, volatility, and maximum drawdowns.

# 2 Related Work

In this section, we briefly discuss two topics, that is, multiarmed bandit and portfolio selection problem.

# 2.1 Multi-armed Bandit and Thompson Sampling

This section contains theories, solutions for the multi-armed bandit problem and Thompson sampling.

There are many exploration vs exploitation dilemmas in many aspects of our life. At the same time, investment strategies attempt to balance existing portfolios and new portfolios to achieve higher returns. In this case, if we can speculate the future trend of all assets in the market, we can find the best investment strategy by just simulating brute-force instead of using several other smart approaches. This dilemma originates from the incomplete information: we need to gather enough information to make best overall decisions while keeping the risk under control. With exploitation, we can take advantage of the best known option. With exploration, we can take some risk to collect information about unknown options. Therefore, the best long-term strategy may involve short-term sacrifices.

The multi-armed bandit problem is a classic problem that exhibits the exploration vs exploitation dilemma. It is like facing multiple slot machines in a casino and each is configured with an unknown probability of how likely you can get a reward at one play. The aim is to maximize the cumulative reward. If we know the optimal action with the best reward, then the goal is same as to minimize the potential regret or loss by not picking the optimal action.

The possible methods that can be used to solve this problem are roughly divided into three distinct categories, - greedy algorithm, upper confidence bounds (UCB) algorithm [Auer et al., 2002] and Thompson sampling [Thompson, 1933].

Thompson sampling has a simple idea. However, it works great for solving the multi-armed bandit problem [Chapelle and Li, 2011; Russo and Van Roy, 2014]. At each time step, select action $a$ according to the Beta probability that $a$ is optimal. After observing the true reward, update the Beta distribution accordingly. This essentially involves doing Bayesian inference to compute the posterior with the known prior and the likelihood of getting the sampled data.

With the rise of reinforcement learning, numerous works study how to apply multi-armed bandit to various fields, such as recommender [Li et al., 2010; Wu et al., 2016] and ecommence [Broden´ et al., 2017; Broden´ et al., 2018]. Besides, some scholars have tried to incorporate reinforcement learning into the field of portfolio optimization [Liang et al., 2018; Jiang et al., 2017; Sani et al., 2012]. Still, other studies have used assets directly as arms in multi-armed bandit. For instance, Shen [Shen et al., 2015] proposed to use the UCB algorithm to achieve online portfolio selection by constructing an orthogonal portfolio. Meanwhile, other studies have only used Thompson sampling to generate portfolio. For example, Shen [Shen and Wang, 2016] presented an online portfolio algorithm that leverages Thompson sampling to mix two different strategies. Inspired by these studies, we combine the multi-armed bandit and Thompson sampling, use the classic strategies as strategy arms to achieve an adaptive portfolio.

# 2.2 Portfolio Strategy

This section presents the current state of research on portfolios, including mean-variance models, forecast trends, and the Universal portfolio. Existing studies have specially based upon classical financial theory and have combined with machine learning to achieve better performance.

In 1952, Markowitz put forward the mean-variance model, which was the first of its kind in modern portfolios [Markowitz, 1952]. This model constrains the relevant conditions of portfolio issues to pursue a balance of risk and return. In particular, some scholars attempted to improve the effect of the mean-variance model by adding regularity [Brodie et al., 2009; Shen et al., 2014]. Other studies have improved the performance of the mean-variance model by changing the sampling method. For instance, Shen [Shen and Wang, 2017] proposed a new portfolio strategy through resampling subsets of the original large universe of assets.

In addition, some scholars pursued the maximum returnto-risk ratio of the portfolio through trend forecasting, such as by predicting stock price movements in the stock market. For example, Palmowski et al. [Palmowski et al., 2018] studied a portfolio selection problem in a continuous-time Ito-ˆ Markov additive market in which the prices of financial assets were described by Markov additive processes. Meanwhile, Paolinelli [Paolinelli and Arioli, 2019] proposed a model for stocks dynamics based on a non-Gaussian path integral, which connected between time horizons and trading strategies.

The third type of research is based on the Universal portfolio theory. This is a portfolio selection algorithm from the field of machine learning and information theory. The algorithm learns adaptively from historical data and maximizes the log-optimal growth rate in the long run. Huang et al. [Huang et al., 2015] designed semi-universal portfolio strategy under transaction fee, which tries to avoid rebalancing when the transaction fee outweighs the benefit of trading.

All of the above methods are all based on a single financial theory to construct an online investment portfolio. However, the method of this paper adaptively adopts different investment strategies in multiple cycles to achieve the highest longterm return-to-risk ratio.

# 3 Methodology

In this section, we first introduce the notations and finance terms used in this paper. We will also discuss several strategic arms based on classic portfolios, formulate portfolio blending a multi-armed bandit problem, and how to solve this problem using Thompson sampling. Lastly, we summarize the proposed algorithm.

# 3.1 Notations and Problem Definition

To start with, we give the problem an abstract definition. We consider a self-financing, limited time and limited asset financial environment. The trading periods consist of $t _ { k } = k \Delta t , k = 0 , . . . , m$ , where $\Delta t$ represents one day, week or month, depending on the cycle of rebalancing and $m$ is the total cycles of participation in the transaction. We also represent the return vector of $n$ assets at time $t _ { k - 1 }$ to $t _ { k }$ time as $\mathbf { R _ { k } }$ . The formula of the return $R _ { k , i }$ of the i-th asset is $R _ { k , i } ~ = ~ P _ { k , i } / P _ { k - 1 , i }$ , where $P _ { k - 1 , i }$ and $P _ { k , i }$ represent the price of the i-th asset at times $t _ { k - 1 }$ and $t _ { k }$ . The transaction fee is also an important factor in the final benefit. For the sake of simplifying the model, however, it is not considered in this model. Still, we think about how to reduce trading behavior.

$\mathbf { W _ { k } }$ as the portfolio weight vector at time $t _ { k }$ denotes the investment decision at time $t _ { k }$ , where $W _ { k , i }$ represents the allocation weight of the i-th asset in the entire portfolio. We assume that the sum of the combined weights is 1 (except for pure cash position), i.e., $\mathbf { W _ { k } ^ { T } 1 } = 1$ , where 1 is a column vector with ones as its entities. Also, we correspond to the following two cases of $\mathbf { W _ { k } }$ and the actual trading strategy: $w _ { k , i } > 0$ indicates that we need to take a long position of the i-th asset at market price; while $w _ { k , i } < 0$ shows that we need to take a short sale position of i-th asset. The actual operation requires a deposit, and also needs to pay dividends for short-selling assets, etc. However, for the sake of simplification, we will not consider this situation for the time being, and only consider the gains or losses caused by stock price changes.

# 3.2 Strategic Arms Based on Classic Portfolios

In our research, we do not directly use assets as arms in multiarmed bandit. Instead, we use classic portfolio strategies in finance as strategic arms to reduce the number of arms, and also to reduce transaction volume as well as increase stability. We use the following strategies:

Buy and Hold (BH): This is an intuitive idea which involves doing nothing and continuing to hold the existing portfolio in this time window.

$$
\mathbf { W _ { k } ^ { B H } } = \mathbf { W _ { k - 1 } } .
$$

Sold All (SA): Involves selling all the assets so that the combination is an empty position or a pure cash position.

$$
\mathbf { W _ { k } ^ { S A } } = \mathbf { 0 } .
$$

Equally-weighted portfolio (EW): Regardless of the asset, all assets are directly placed into equal weight positions during each rebalancing period.

$$
\mathbf { W _ { k } ^ { E W } } = { \frac { 1 } { n } } \mathbf { 1 } .
$$

Value-weighted portfolio (VW): As a passive investment strategy, positions in each rebalancing period are allocated as per the current capital of each asset.

$$
{ \bf W _ { k } ^ { V W } } = \frac { { \bf W _ { k - 1 } } \circ { \bf R _ { k - 1 } } } { { \bf W _ { k - 1 } ^ { T } } { \bf R _ { k - 1 } } } .
$$

Mean-variance portfolio (MV): Mean-variance model is a strategy constructed in line with the Markowitz’s theory. It captures the aforementioned risk-return trade-off.

$$
\mathbf { W _ { k } ^ { M V } } = \arg \operatorname* { m i n } _ { \mathbf { W _ { k } 1 } = 1 } \mathbf { W _ { k } ^ { T } } \boldsymbol { \Sigma _ { k } } \mathbf { W _ { k } } - \mathbf { R _ { k } ^ { T } } \mathbf { W _ { k } } ,
$$

where $\mathbf { R _ { k } ^ { T } W _ { k } }$ is the expected return and $\mathbf { W _ { k } ^ { T } } \mathbf { \Sigma } \mathbf { \Sigma } \mathbf { W _ { k } }$ is the variance of portfolio returns.

# 3.3 Portfolio Bandit via Thompson Sampling (PBTS)

Each strategy has its own suitable period and scene, thus they also have a certain probability to get the most profit. Basing on this idea, this paper regards the portfolio selection problem as a multi-armed bandit problem, and classic portfolio strategies as the strategic arms in order to achieve higher long-term returns. The specific definition is as follows:

The multi-armed bandit of the portfolio strategy is $<$ $a ; R _ { a } \mathrm { ~ > ~ }$ . $a$ is a collection of strategic arms (classic portfolio strategies),

$$
\begin{array} { r } { a _ { k } = [ a _ { k , 1 } , . . . , a _ { k , l } ] , } \\ { a _ { k , 1 } = w _ { k } ^ { B H } , a _ { k , 2 } = w _ { k } ^ { S A } , a _ { k , 3 } = w _ { k } ^ { E W } , } \\ { a _ { k , 4 } = w _ { k } ^ { V W } , a _ { k , 5 } = w _ { k } ^ { M V } , } \end{array}
$$

where $l$ represents the total number of strategic arms. There are $l$ arms at each time $k$ , and which arm is selected according to which strategy is used to adjust the weight of the portfolio.

Assume $R _ { a _ { j , r } } ~ = ~ P ( r | a _ { j } )$ is the probability distribution function of the return, at each time $k$ , $\theta _ { k , j } \sim R _ { a _ { j , r } }$ . And the probability of each strategic arm is a Beta distribution $\theta _ { j } \sim$ $B e t a ( \alpha _ { j } , \beta _ { j } )$ .

At time $\mathbf { k }$ , each arm randomly samples a value $\theta _ { k , j }$ from its respective Beta distribution, then the arm $j _ { k }$ of this selection is:

$$
j _ { k } = \arg \operatorname* { m a x } _ { j } \theta _ { k , j } .
$$

In order to judge whether this choice is successful, we comprehensively consider the users’ investment risk preferences and use the Sharpe ratio as a measure. Therefore, we give a $( 0 , 1 )$ criterion based on the top- $\mathbf { \nabla } \cdot \mathbf { k }$ strategy. The judgment formula is:

$$
\begin{array} { r } { \left\{ \begin{array} { c l } & { \sum _ { j = 1 } ^ { l } ( \mathbf { 1 } _ { A } ) \geq c \quad s u c c e s s } \\ & { \sum _ { j = 1 } ^ { l } ( \mathbf { 1 } _ { A } ) < c \quad f a i l u r e } \end{array} \right. } \\ & { A = \left\{ j \mid S R ( a _ { k , j _ { k } } ) - S R ( a _ { k , j } ) \geq 0 \right\} , } \end{array}
$$

where $\mathbf { 1 } _ { A }$ is an indicator function and $S R ( a _ { k , j } )$ represents the Sharp ratio of user’s historical selection of arm $j$ at time $t _ { k }$ . Usually, the international average generally takes a 36- month net growth rate to calculate the Sharpe ratio.

The choice of $c$ can be selected based on users’ investment risk preferences. If the user prefers to pursue high-risk and high-return, the smaller the $c$ can be; the larger the $c$ can be, if the user tends to pursue a relatively stable investment.

Then update the Beta distribution of arm $j _ { k }$ , expressed as:

$$
\begin{array} { r } { \left\{ \begin{array} { l l } { s u c c e s s } & { \theta _ { j _ { k } } \sim B e t a ( \alpha _ { j _ { k } } + 1 , \beta _ { j _ { k } } ) } \\ { f a i l u r e } & { \theta _ { j _ { k } } \sim B e t a ( \alpha _ { j _ { k } } , \beta _ { j _ { k } } + 1 ) } \end{array} , \right. } \end{array}
$$

Algorithm 1 Portfolio Bandit via Thompson Sampling   
Input: Total cycles of participation in the transaction $( m )$ ,   
number of asserts $( n )$ , daily return $( \mathbf { R } )$ , sliding window $( \tau )$ ,   
the top (c)   
Output: Portfolio weight (w) 1: Initialize the Beta distribution $\theta _ { j } \sim B e t a ( \alpha _ { j } , \beta _ { j } )$ of each strategic arm by $\alpha _ { 1 } = . . . = \alpha _ { l } = \beta _ { 1 } = \beta _ { l } = 1$ . 2: for $k = 1$ to $m$ do   
3: Calculate the weight ratio of each basic portfolio strategy according to Eqs. (1) - (5).   
4: Sampling each arm’s $\theta _ { j , k }$ from the $B e t a ( \alpha _ { j } , \beta _ { j } )$ distribution .   
5: Select arm $j _ { k }$ according to Equation (7).   
6: if $k > \tau$ then   
7: Assign the portfolio weight $w _ { k } = a _ { k , j _ { k } }$ at $t _ { k }$ .   
8: end if   
9: Update $\alpha _ { j }$ and $\beta _ { j }$ according to Eqs. (8)-(9).   
10: if Success then   
11: $\alpha _ { j } = \alpha _ { j } + 1 .$   
12: else   
13: $\beta _ { j } = \beta _ { j } + 1 .$   
14: end if   
15: end for

where success/f ailure is determined by Equation (8).

Additionally, for each arm’s Beta distribution, we first use $B e t a ( 1 , 1 )$ as the initial prior of each arm and update the a priori results using sliding window $\tau$ of historical data. Since there is no investment strategy performance, $B e t a ( 1 , 1 )$ , the even distribution of standards, is a reasonable initialization for investors. At each rebalancing time, the investor builds the Bernoulli test described above, observes subsequent successes or failures, and updates the posterior distribution accordingly.

Algorithm 1 summarizes the process of building a multiarmed bandit problem and solving problem via Thompson sampling.

# 4 Experiments

# 4.1 Data

In our experiment, we consider two types of datasets. The first one is the FF dataset, which was built by Fama and French based on the US stock market and continues to be updated to date [Fama and French, 1992]. Overall, they have an extensive coverage of assets classes and span a long period. In our experiments, the FF25, FF49, FF100 datasets include monthly returns of 25, 49, and 100 assets more than half a century. Among them, FF25 and FF100 are formed on size and book-to-market, while FF49 is an industry portfolio. The second one is a more frequent stock market data, which includes constituents of the SP500 and ETFs in the US stock market. We exclude assets with missing data for the past five years. Thus, we remain with 476 stocks from 500 constituent stocks as well as 608 ETFs retained by 1,340 ETFs.

Table 1 is a summary of the datasets, representing different investment perspectives in the market. The FF datasets emphasize long-term gains, spanning more than half a century.

They include the different periods of the US stock market as well as multiple financial crises that can reflect the long-term gains of the strategy. Meanwhile, the SP500 and ETF datasets reflect at high trading frequencies. Regardless of the extreme market, the medium-term performance of the strategy is highlighted. In particular, we choose the timing of our datasets to avoid the latest financial crisis after 2007.

# 4.2 Evaluation Metrics

We use the standard criteria in finance [Brandt, 2010] to measure the performance of the portfolio strategy outside the training sample: (1) Sharpe Ratio; (2) Cumulative Wealth; (3) Maximum Drawdown; (4) Volatility.

Sharpe Ratio (SR) measures the return-to-risk ratio of a portfolio strategy and normalizes the return on the portfolio using its standard deviation. It is expressed as:

$$
S R = \frac { \hat { \mu } } { \hat { \sigma } } , \hat { \mu } = \frac { 1 } { m - \tau } \sum _ { t = \tau + 1 } ^ { m } \mu _ { t } , \hat { \sigma } = \sqrt { \frac { 1 } { m - \tau } \sum _ { t = \tau + 1 } ^ { m } ( \mu _ { t } - \hat { \mu } ) ^ { 2 } } ,
$$

where $\mu _ { t } = \mathbf { R _ { t } } ^ { T } \mathbf { w _ { t } } - 1$

SR is a comprehensive measure that combines both returns and risks into the evaluation, giving the return value of each risk of the portfolio.

Cumulative Wealth (CW) is a weighted cumulative return measuring the time at which each asset’s revenue in a portfolio strategy begins to accumulate to the last calculated return. It is expressed as:

$$
C W = \prod _ { t = \tau + 1 } ^ { m } \mathbf { R _ { t } } ^ { T } \mathbf { w _ { t } } .
$$

Maximum Drawdown (MDD) is the maximum amount of wealth reduction that a cumulative wealth has produced from its maximum value over time, expressed as:

$$
M D D = \operatorname* { m a x } _ { t \in ( \tau , m ) } ( M _ { t } - C W _ { t } ) , M _ { t } = \operatorname* { m a x } _ { k \in ( \tau , t ) } C W _ { k } ,
$$

where retracement $M _ { t } - C W _ { t }$ represents to the loss from the maximum wealth value $M _ { t }$ during its operation to the time $t .$ , and $C W _ { t }$ denotes to the cumulative wealth up to the time $t$ . Since the sharp decline inevitably causes investors to panic and cause divestment, the maximum retracement is usually the primary risk measure for the money management industry.

Volatility (VO) is a quantitative risk metric for the investment industry. The calculation of portfolio volatility is related to the standard deviation in Equation (10). To measure the portfolio strategy with different weight adjustment frequencies, we calculate the annualized volatility using the following formula:

$$
V O = { \sqrt { H } } { \hat { \sigma } } ,
$$

where $H$ is the number of times the weights are adjusted each year. In our experiment, $H = 1 2$ for the monthly datasets, and $H = 3 6 5$ for the daily datasets.

Table 1: Summary of the datasets   

<table><tr><td>Dataset</td><td>Frequency</td><td>Time Period</td><td>m</td><td>n</td><td>Description</td></tr><tr><td>FF25</td><td>Monthly</td><td>06/01/1963 - 11/31/2018</td><td>545</td><td>25</td><td>25 portfolios of firms sorted by size and book-to-market</td></tr><tr><td>FF49</td><td>Monthly</td><td>07/01/1969 - 11/31/2018</td><td>472</td><td>49</td><td>49 industry portfolios representing the U.S. stock market</td></tr><tr><td>FF100</td><td>Monthly</td><td>07/01/1963 - 11/31/2018</td><td>544</td><td>100</td><td>100 portfolios of firms sorted by size and book-to-market</td></tr><tr><td>ETFs</td><td>Daily</td><td>12/08/2011 - 11/10/2017</td><td>1,138</td><td>608</td><td>Exchange-traded funds in U.S. stock market</td></tr><tr><td>SP500</td><td>Daily</td><td>02/11/2013 - 02/07/2018</td><td>1,355</td><td>476</td><td>500 firms listed in the S&amp;P 500 Index</td></tr></table>

![](images/0dea7938c2c7b5aae4da9adb8a860faaa4196a375e0f544a41bc0df7c8a8c742.jpg)  
Figure 1: The curves of cumulative wealth across the investment periods for different portfolios on (a) FF25, (b) FF49, (c) FF100, (d) ETFs, and (e) SP500 datasets.

# 4.3 Competing Portfolios

To comprehensively assess the proposed method, we consider ten modern competing portfolios according to our literature review:

Equally-weighted portfolio (EW): EW is one of classic strategies, which. It has outperformed 14 sophisticated models across seven real-world datasets at monthly frequency of 2000 years [DeMiguel et al., 2007]. Therefore, EW is the first benchmark algorithm for portfolio research.

Value-weighted portfolio (VW): VW is a strategy that imitates the market’s passive portfolio, which is the same as the market index’s volatility. It is also an important benchmark strategy.

Mean-variance portfolio (MV): MV is one of our basic strategies based on Markowitz’s theory and outperforms in different markets and time spans.

Orthogonal Bandit portfolio (OBP): OBP constructs multiple assets by constructing orthogonal portfolios. It also uses the upper confidence bound bandit framework to derive the optimal portfolio strategy that represents the combination of passive and active investments as per a risk-adjusted reward function [Shen et al., 2015].

Portfolio Blending via Thompson Sampling (TS-EM, TS-VM): This strategy is applied by Thompson sampling to the portfolio field for mixing EW and MV as TS-EM, VW and MV as TS-VM [Shen and Wang, 2016].

Portfolio Selection via Subset Resampling (SSR): The SSR method estimates the parameters by re-sampling subsets of the original assets, and aggregates the subsets of the multiple constructs to obtain the portfolio of all assets [Shen and Wang, 2017].

Generally, EW, VW, and MV are three portfolio strategy arms of PBTS, which should be compared with the hybrid model proposed in this paper. OBP, TS-EM, TS-VM, and SSR are the heuristic experiments of the model. They are well recognized as important portfolio strategies based on the exploration and exploitation problem. Therefore, to be more convincing, we also compare with these four models.

# 4.4 Parameter Settings

We use the “rolling range” setting proposed by DeMiguel [DeMiguel et al., 2007]. In regard to the model proposed in this paper, we set the sliding window as $\tau = 1 2 0$ . For the parameter $c$ of the PBTS, we utilize cross validation to establish the optimal parameters. And for the parameters of other comparison algorithms, we use the parameter settings recommended in the relevant studies.

# 4.5 Results and Analysis

Results Table 2 summarize portfolio performance evaluated by the SR, CW, MDD, and VO for all the tested benchmarks, respectively. From the comparisons of the various methods, the values in bold represent the winners’ performance. The proposed PBTS method achieves a better performance in most of the cases. On the one hand, for the SR, the results of the PBTS are in the first echelon on all datasets, with a slightly lower EW on the ETFs dataset as well as less than VW on the SP500 dataset. This indicates that the PBTS basically has a better return-to-risk ratio. For the absolute return indicator, we use Figure 1 to reflect the change in earnings over time. PBTS outperforms other methods on most datasets, only below the MV and SSR on the FF25 dataset and lower than VW and OBP on the ETFs dataset. However, the OBP and SSR method has large fluctuations on other datasets. As well, the robustness is lower than the PBTS method. On the other hand, PBTS performs better on the risk indicators. As summarized in Table 2, the MDD of PBTS is the smallest; while PBTS’s VO is lower than EW in the ETFs dataset, which is usually the lowest VO in the classic strategies, and is superior to other comparison methods in other datasets.

Table 2: Performance of portfolio strategies   

<table><tr><td>Dataset</td><td>Metrics</td><td>PBTS</td><td>EW</td><td>VW</td><td>MV</td><td>OBP</td><td>TS-EM</td><td>TS-VM</td><td>SSR</td></tr><tr><td rowspan="4">FF25</td><td>SR</td><td>22.60</td><td>20.02</td><td>19.84</td><td>19.30</td><td>15.92</td><td>19.82</td><td>19.93</td><td>19.08</td></tr><tr><td>CW</td><td>589.41</td><td>291.93</td><td>398.67</td><td>766.58</td><td>241.60</td><td>588.41</td><td>520.81</td><td>772.46</td></tr><tr><td>MDD (%)</td><td>43.83</td><td>54.10</td><td>55.91</td><td>57.98</td><td>59.41</td><td>57.07</td><td>56.60</td><td>58.49</td></tr><tr><td>VO (%)</td><td>17.71</td><td>17.51</td><td>17.68</td><td>18.20</td><td>22.03</td><td>17.71</td><td>17.60</td><td>18.41</td></tr><tr><td rowspan="4">FF49</td><td>SR</td><td>24.20</td><td>23.15</td><td>23.22</td><td>11.77</td><td>18.55</td><td>15.77</td><td>15.93</td><td>13.22</td></tr><tr><td>CW</td><td>29.94</td><td>19.46</td><td>17.26</td><td>12.43</td><td>24.65</td><td>15.23</td><td>16.21</td><td>12.68</td></tr><tr><td>MDD (%)</td><td>38.30</td><td>52.83</td><td>51.42</td><td>79.90</td><td>51.97</td><td>68.72</td><td>68.35</td><td>75.79</td></tr><tr><td>VO (%)</td><td>14.39</td><td>15.10</td><td>15.05</td><td>29.76</td><td>18.87</td><td>22.19</td><td>21.96</td><td>26.44</td></tr><tr><td rowspan="4">FF100</td><td>SR</td><td>21.76</td><td>20.71</td><td>21.43</td><td>19.21</td><td>15.81</td><td>20.85</td><td>20.62</td><td>20.21</td></tr><tr><td>CW</td><td>57.27</td><td>28.12</td><td>53.28</td><td>18.04</td><td>43.14</td><td>29.42</td><td>22.69</td><td>28.78</td></tr><tr><td>MDD (%)</td><td>30.76</td><td>58.73</td><td>53.72</td><td>50.26</td><td>54.80</td><td>51.80</td><td>53.29</td><td>52.38</td></tr><tr><td>VO (%)</td><td>16.06</td><td>16.88</td><td>16.33</td><td>18.18</td><td>22.16</td><td>16.77</td><td>16.94</td><td>17.30</td></tr><tr><td rowspan="4">ETFs</td><td>SR</td><td>194.49</td><td>197.22</td><td>147.67</td><td>17.93</td><td>70.94</td><td>31.38</td><td>31.42</td><td>19.40</td></tr><tr><td>CW</td><td>1.15</td><td>1.28</td><td>1.51</td><td>0.15</td><td>1.88</td><td>0.63</td><td>0.58</td><td>0.38</td></tr><tr><td>MDD (%)</td><td>15.40</td><td>16.20</td><td>18.46</td><td>96.44</td><td>23.71</td><td>78.77</td><td>79.58</td><td>88.09</td></tr><tr><td>VO (%)</td><td>9.83</td><td>9.69</td><td>12.94</td><td>106.56</td><td>26.95</td><td>60.89</td><td>60.81</td><td>98.54</td></tr><tr><td rowspan="4">SP500</td><td>SR</td><td>126.88</td><td>124.49</td><td>127.56</td><td>41.27</td><td>52.54</td><td>66.71</td><td>66.56</td><td>39.77</td></tr><tr><td>CW</td><td>1.65</td><td>1.52</td><td>1.53</td><td>1.27</td><td>1.30</td><td>1.49</td><td>1.47</td><td>1.32</td></tr><tr><td>MDD (%)</td><td>14.97</td><td>16.41</td><td>14.97</td><td>36.81</td><td>41.09</td><td>20.82</td><td>21.24</td><td>46.49</td></tr><tr><td>VO (%)</td><td>15.06</td><td>15.35</td><td>14.98</td><td>46.32</td><td>36.38</td><td>28.65</td><td>28.72</td><td>48.07</td></tr></table>

Analysis In summary, through the performance of the three long-term FF datasets, we believe that the PBTS method has an outstanding performance in terms of long-term performance. This is consistent with the goal of PBTS of achieving excellent long-term returns. However, in the mid-term high frequency situation, through the ETF and SP500 datasets, we realize that PBTS is not robust enough and depends on the performance of basic strategies.

Parameter effect analysis We analyze the performance of PBTS in the case of different $c$ , as shown in Figure 2. In FF25 dataset, as $c$ becomes larger, the volatility decreases, but the cumulative wealth decreases. This is consistent with our hypothesis that the larger the $c$ , the lower the user’s risk reference and the lower the risk that can be borne, but the return is reduced.

![](images/9d873a0556cbaa5514bc5f0388a38f749dc169597729fb1f9bcbeb3abdbe0068.jpg)  
Figure 2: The effect of different $c$ on the performance of PBTS in FF25 dataset

# 5 Conclusions and Future Work

In this paper, we constructed the portfolio selection problem into a multi-armed bandit problem, wherein we used the classic portfolio strategies as the strategic arms to form a dynamic portfolio strategy with multiple cycles to adapt for different periods. Moreover, we devise a reward function based on the user’s investment risk preference to judge the standard and select the optimal arm of each period via Thompson sampling. Our algorithm could appropriately balance the benefits and risks well and achieve higher returns by controlling risk.

In the future work, we will consider the correlation between the strategic arms and the impact of the previous selection path on the next choice. Also, the actual status of financial scenarios such as transaction fee, tax, and dividend should be considered as factors to build a portfolio strategy that is more consistent with the real scenario.

References   
[Auer et al., 2002] Peter Auer, Nicolo Cesa-Bianchi, and Paul Fischer. Finite-time analysis of the multiarmed bandit problem. Machine learning, 47(2-3):235–256, 2002.   
[Brandt, 2010] Michael W Brandt. Portfolio choice problems. In Handbook of financial econometrics: Tools and techniques, pages 269–336. Elsevier, 2010.   
[Brinson et al., 1995] Gary P Brinson, L Randolph Hood, and Gilbert L Beebower. Determinants of portfolio performance. Financial Analysts Journal, 51(1):133–138, 1995.   
[Broden´ et al., 2017] Bjorn Brod ¨ en, Mikael Hammar, ´ Bengt J Nilsson, and Dimitris Paraschakis. Bandit algorithms for e-commerce recommender systems. In Proceedings of the Eleventh ACM Conference on Recommender Systems, pages 349–349. ACM, 2017.   
[Broden´ et al., 2018] Bjorn Brod ¨ en, Mikael Hammar, ´ Bengt J Nilsson, and Dimitris Paraschakis. Ensemble recommendations via thompson sampling: an experimental study within e-commerce. In $2 3 r d$ International Conference on Intelligent User Interfaces, pages 19–29. ACM, 2018.   
[Brodie et al., 2009] Joshua Brodie, Ingrid Daubechies, Christine De Mol, Domenico Giannone, and Ignace Loris. Sparse and stable markowitz portfolios. Proceedings of the National Academy of Sciences, 106(30):12267–12272, 2009.   
[Chapelle and Li, 2011] Olivier Chapelle and Lihong Li. An empirical evaluation of thompson sampling. In Advances in neural information processing systems, pages 2249– 2257, 2011.   
[DeMiguel et al., 2007] Victor DeMiguel, Lorenzo Garlappi, and Raman Uppal. Optimal versus naive diversification: How inefficient is the $1 / \mathrm { n }$ portfolio strategy? The review of Financial studies, 22(5):1915–1953, 2007.   
[Fama and French, 1992] Eugene F Fama and Kenneth R French. The cross-section of expected stock returns. the Journal of Finance, 47(2):427–465, 1992.   
[Huang et al., 2015] Dingjiang Huang, Yan Zhu, Bin Li, Shuigeng Zhou, and Steven CH Hoi. Semi-universal portfolios with transaction costs. In Twenty-Fourth International Joint Conference on Artificial Intelligence, 2015.   
[Jiang et al., 2017] Zhengyao Jiang, Dixing $\mathrm { X u }$ , and Jinjun Liang. A deep reinforcement learning framework for the financial portfolio management problem. arXiv preprint arXiv:1706.10059, 2017.   
[Li et al., 2010] Lihong Li, Wei Chu, John Langford, and Robert E Schapire. A contextual-bandit approach to personalized news article recommendation. In Proceedings of the 19th international conference on World wide web, pages 661–670. ACM, 2010.   
[Liang et al., 2018] Zhipeng Liang, Hao Chen, Junhao Zhu, Kangkang Jiang, and Yanran Li. Adversarial deep reinforcement learning in portfolio management. arXiv preprint arXiv:1808.09940, 2018.

[Markowitz, 1952] Harry Markowitz. Portfolio selection. The journal of finance, 7(1):77–91, 1952.

[Palmowski et al., 2018] Zbigniew Palmowski, Łukasz Stettner, and Anna Sulima. Optimal portfolio selection in an ito-markov additive market. ˆ arXiv preprint arXiv:1806.03496, 2018.   
[Paolinelli and Arioli, 2019] Giovanni Paolinelli and Gianni Arioli. A model for stocks dynamics based on a nongaussian path integral. Physica A: Statistical Mechanics and its Applications, 517:499–514, 2019.   
[Russo and Van Roy, 2014] Daniel Russo and Benjamin Van Roy. Learning to optimize via posterior sampling. Mathematics of Operations Research, 39(4):1221–1243, 2014.   
[Sani et al., 2012] Amir Sani, Alessandro Lazaric, and Remi ´ Munos. Risk-aversion in multi-armed bandits. In Advances in Neural Information Processing Systems, pages 3275–3283, 2012.   
[Shen and Wang, 2016] Weiwei Shen and Jun Wang. Portfolio blending via thompson sampling. In Proceedings of the Twenty-Fifth International Joint Conference on Artificial Intelligence, pages 1983–1989. AAAI Press, 2016.   
[Shen and Wang, 2017] Weiwei Shen and Jun Wang. Portfolio selection via subset resampling. In Thirty-First AAAI Conference on Artificial Intelligence, 2017.   
[Shen et al., 2014] Weiwei Shen, Jun Wang, and Shiqian Ma. Doubly regularized portfolio with risk minimization. In Proceedings of the Twenty-Eighth AAAI Conference on Artificial Intelligence, pages 1286–1292. AAAI Press, 2014.   
[Shen et al., 2015] Weiwei Shen, Jun Wang, Yu-Gang Jiang, and Hongyuan Zha. Portfolio choices with orthogonal bandit learning. In Twenty-Fourth International Joint Conference on Artificial Intelligence, 2015.   
[Thompson, 1933] William R Thompson. On the likelihood that one unknown probability exceeds another in view of the evidence of two samples. Biometrika, 25(3/4):285– 294, 1933.   
[Wu et al., 2016] Qingyun Wu, Huazheng Wang, Quanquan Gu, and Hongning Wang. Contextual bandits in a collaborative environment. In Proceedings of the 39th International ACM SIGIR conference on Research and Development in Information Retrieval, pages 529–538. ACM, 2016.