import numpy as np

try: from qfrm.OptionValuation import *  # production:  if qfrm package is installed
except:   from qfrm.option import *  # development: if not installed and running from source

from scipy import sparse

class LowExercisePrice(OptionValuation):
    """ LowExercisePrice option class.


    Inherits all methods and properties of OptionValuation class.
    """
    def calc_px(self, method='BS', nsteps=None, npaths=None, keep_hist=False):
        """ Wrapper function that calls appropriate valuation method.

        All parameters of ``calc_px`` are saved to local ``px_spec`` variable of class ``PriceSpec`` before
        specific pricing method (``_calc_BS()``,...) is called.
        An alternative to price calculation method ``.calc_px(method='BS',...).px_spec.px``
        is calculating price via a shorter method wrapper ``.pxBS(...)``.
        The same works for all methods (BS, LT, MC, FD).

        Parameters
        ----------
        method : str
                Required. Indicates a valuation method to be used:
                ``BS``: Black-Scholes Merton calculation
                ``LT``: Lattice tree (such as binary tree)
                ``MC``: Monte Carlo simulation methods
                ``FD``: finite differencing methods
        nsteps : int
                LT, MC, FD methods require number of times steps
        npaths : int
                MC, FD methods require number of simulation paths
        keep_hist : bool
                If True, historical information (trees, simulations, grid) are saved in self.px_spec object.

        Returns
        -------
        self : LowExercisePrice
            Returned object contains specifications and calculated price in embedded ``PriceSpec`` object.


        Examples
        --------

        **LT Examples**

        #From DeriGem. S0=5, K=0.01, vol=0.30, T=4, rf_r=0.1, Steps=4, BSM European Call
        >>> s = Stock(S0=5, vol=.30)
        >>> o = LowExercisePrice(ref=s,T=4,rf_r=.10)
        >>> print(o.calc_px(method='LT',nsteps=4,npaths=10).px_spec.px)
        ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        4.99329679...

        >>> s = Stock(S0=19.6, vol=.21)
        >>> o = LowExercisePrice(ref=s,T=5,rf_r=.05)
        >>> o.calc_px(method='LT',nsteps=4,npaths=10) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        LowExercisePrice...px: 19.592211992...
        <BLANKLINE>

        >>> s = Stock(S0=19.6, vol=.30)
        >>> o = LowExercisePrice(ref=s,T=5,rf_r=.10)
        >>> print(o.calc_px(method='LT',nsteps=2,keep_hist=True).px_spec.ref_tree) # prints reference tree
        ((19.600000000000005,), (12.196974354006297, 31.496335800182806), (7.59011139756568, 19.6, 50.613222899891674))

        # From DeriGem. S0=5, K=0.01, vol=0.30, T=2, rf_r=0.1, Steps=4, Binomial European Call
        >>> s = Stock(S0=5, vol=.30)
        >>> o = LowExercisePrice(ref=s,T=2,rf_r=.10)
        >>> print(o.calc_px(method='LT',nsteps=4,keep_hist=False).px_spec.px) # doctest: +ELLIPSIS
        4.991812...

        >>> from pandas import Series
        >>> from numpy import arange
        >>> price = arange(5,10,1)
        >>> O = Series([LowExercisePrice(ref=Stock(S0=p, vol=.30), T=2, \
        rf_r=.08).calc_px(method='LT').px_spec.px for p in price], price)
        >>> O.plot(grid=1, title='LowExercisePrice option Price vs Spot Price (in years)') # doctest: +ELLIPSIS
        <matplotlib.axes._subplots.AxesSubplot object at ...>
        >>> plt.show()

        ===============
        FD Examples
        ===============
        >>> s = Stock(S0=5, vol=.30)
        >>> o = LowExercisePrice(ref=s,T=4,rf_r=.10)
        >>> o.pxFD(nsteps=4,npaths=10)
        ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        4.407303373

        >>> s = Stock(S0=19.6, vol=.21)
        >>> o = LowExercisePrice(ref=s,T=5,rf_r=.05)
        >>> o.calc_px(method='FD',nsteps=4,npaths=10) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        LowExercisePrice...px: 18.657861519...
        <BLANKLINE>

        # From DeriGem. S0=5, K=0.01, vol=0.30, T=2, rf_r=0.1, Steps=4, Binomial European Call
        >>> s = Stock(S0=5, vol=.30)
        >>> o = LowExercisePrice(ref=s,T=2,rf_r=.10)
        >>> print(o.calc_px(method='FD',nsteps=4,npaths = 10,keep_hist=False).px_spec.px) # doctest: +ELLIPSIS
        4.841966227...


        Notes
        -----
        [1] Wikipedia: Low Exercise Price Option - https://en.wikipedia.org/wiki/Low_Exercise_Price_Option
        [2] LEPOs Explanatory Booklet http://www.asx.com.au/documents/resources/UnderstandingLEPOs.pdf

        :Authors:
            Runmin Zheng
       """

        # LowExercisePrice is an European call option with a fixed strike price $0.01
        self.K=0.01
        self.right='call'
        return super().calc_px(method=method, nsteps=nsteps, npaths=npaths, keep_hist=keep_hist)

    def _calc_BS(self):
        """ Internal function for option valuation.

        Returns
        -------
        self: LowExercisePrice

        .. sectionauthor::

        """



        return self


    def _calc_LT(self):
        """ Internal function for option valuation.
        Modified from European Call Option.

        Returns
        -------
        self: LowExercisePrice.

        .. sectionauthor:: Runmin Zhang



        Examples
        -------
        """


        # Get the # of steps of binomial tree
        n = getattr(self.px_spec, 'nsteps', 3)
        _ = self.LT_specs(n)

        # Generate the binomial tree from the parameters
        S = self.ref.S0 * _['d'] ** np.arange(n, -1, -1) * _['u'] ** np.arange(0, n + 1)

        O = np.maximum((S - 0.01), 0)          # terminal option payouts
        S_tree, O_tree = None, None

        if getattr(self.px_spec, 'keep_hist', False): # if don't keep the whole binomial tree
            S_tree = (tuple([float(s) for s in S]),)
            O_tree = (tuple([float(o) for o in O]),)

            for i in range(n, 0, -1):
                O = _['df_dt'] * ((1 - _['p']) * O[:i] + ( _['p']) * O[1:])  #prior option prices (@time step=i-1)
                S = _['d'] * S[1:i+1]                   # prior stock prices (@time step=i-1)

                S_tree = (tuple([float(s) for s in S]),) + S_tree
                O_tree = (tuple([float(o) for o in O]),) + O_tree

            out = O_tree[0][0]
        else:                                                      # If we do keep the trees
            csl = np.insert(np.cumsum(np.log(np.arange(n) + 1)), 0, 0)         # logs avoid overflow & truncation
            tmp = csl[n] - csl - csl[::-1] + np.log(_['p']) * np.arange(n + 1)\
                  + np.log(1 - _['p']) * np.arange(n + 1)[::-1]
            out = (_['df_T'] * sum(np.exp(tmp) * tuple(O)))

        self.px_spec.add(px=float(out), sub_method='Binomial tree with the strike price is $0.01; Hull Ch.135',
                         LT_specs=_, ref_tree=S_tree, opt_tree=O_tree)

        return self


    def _calc_MC(self, nsteps=3, npaths=4, keep_hist=False):
        """ Internal function for option valuation.

        Returns
        -------
        self: Basket
        .. sectionauthor::

        Notes
        -----


        """
        return self

    def _calc_FD(self):
        """ Internal function for option valuation.

        See ``calc_px()`` for complete documentation.

        :Authors:
            Thawda Aung (thawda.aung1@gmail.com)
        """


        assert self.right in ['call', 'put'], 'right must be "call" or "put" '
        assert self.ref.vol > 0, 'vol must be >=0'
        assert self.K > 0, 'K must be > 0'
        assert self.T > 0, 'T must be > 0'
        assert self.ref.S0 >= 0, 'S must be >= 0'
        assert self.rf_r >= 0, 'r must be >= 0'

        S0 = self.ref.S0
        vol = self.ref.vol
        ttm = self.T
        K = 0.01
        K2 = 0
        r = self.rf_r
        try: q = self.ref.q
        except: pass

        time_steps = getattr(self.px_spec, 'nsteps', 3)
        px_paths = getattr(self.px_spec, 'npaths', 3)

        # Initial the matrix. Hull's P482
        S_max = S0*2
        S_min = 0.0
        d_px = S_max/(px_paths-1)
        d_t = ttm/(time_steps-1)
        S_vec = np.linspace(S_min,S_max,px_paths)
        t_vec = np.linspace(0,ttm,time_steps)

        f_px = np.zeros((px_paths,time_steps))


        M = px_paths - 1
        N = time_steps-1

        f_px[:,-1]=S_vec

        # Set boundary conditions.


        if self.right=='call':
            # Payout at the maturity time
            init_cond = np.maximum((S_vec-K),0)*(S_vec>=K2)
            # Boundary condition
            upper_bound = 0
            # Calculate the current value
            lower_bound = np.maximum((S_vec[-1]-K),0)*(S_vec[-1]>=K2)*np.exp(-r*(ttm-t_vec))
        elif self.right=='put':
            # Payout at the maturity time
            init_cond = np.maximum((K-S_vec),0)*(S_vec<=K2)
            # Boundary condition
            upper_bound = np.maximum((K-S_vec[0]),0)*(S_vec[0]<=K2)*np.exp(-r*(ttm-t_vec))
            # Calculate the current value
            lower_bound = 0


        #Generate Matrix B in http://www.goddardconsulting.ca/option-pricing-finite-diff-implicit.html
        j_list = np.arange(0,M+1)
        a_list = 0.5*d_t*((r-q)*j_list-vol**2*j_list**2)
        b_list = 1+d_t*(vol**2*j_list**2 + r)
        c_list = 0.5*d_t*(-(r-q)*j_list-vol**2*j_list**2)

        data = (a_list[2:M],b_list[1:M],c_list[1:M-1])
        B=sparse.diags(data,[-1,0,1]).tocsc()



        #K = np.zeros(M-1)
        f_px[:,N] = init_cond
        f_px[0,:] = upper_bound
        f_px[M,:]=lower_bound
        Offset = np.zeros(M-1)
        for idx in np.arange(N-1,-1,-1):
            Offset[0] = -a_list[1]*f_px[0,idx]
            Offset[-1] = -c_list[M-1]*f_px[M,idx]
            #f_px[1:M,idx] = scipy.linalg.solve(B,f_px[1:M,idx+1]-K)
            f_px[1:M,idx]=sparse.linalg.spsolve(B,f_px[1:M,idx+1]+Offset)
            f_px[:,-1] = init_cond
            f_px[0,:] = upper_bound
            f_px[-1,:]=lower_bound

        self.px_spec.add(px=float(np.interp(S0,S_vec,f_px[:,0])), sub_method='Implicit Method')
        # if self.keep_hist == True:
        #     self.px_spec.add(opt_tree=f_px)
        return self