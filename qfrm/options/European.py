import math

from qfrm.vec import Vec

try: from qfrm.OptionValuation import *  # production:  if qfrm package is installed
except:   from qfrm.option import *  # development: if not installed and running from source


class European(OptionValuation):
    """ European option class.

    Inherits all methods and properties of ``OptionValuation`` class.
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
                If ``True``, historical information (trees, simulations, grid) are saved in ``self.px_spec`` object.

        Returns
        -------
        European
            Returned object contains specifications and calculated price in embedded ``PriceSpec`` object.


        Examples
        --------

        >>> s = Stock(S0=42, vol=.20)
        >>> o = European(ref=s, right='put', K=40, T=.5, rf_r=.1, desc='call @0.81, put @4.76, Hull p.339')
        >>> o.calc_px(method='BS').px_spec   # save interim results to self.px_spec. Equivalent to repr(o)
        ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        PriceSpec...px: 0.808599373...

        >>> (o.px_spec.px, o.px_spec.d1, o.px_spec.d2, o.px_spec.method)  # alternative attribute access
        ... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        (0.808599372..., 0.769262628..., 0.627841271..., 'BS')

        >>> o.update(right='call').pxBS()  # change option object to a put
        4.759422393

        >>> European(clone=o, K=41, desc='Ex. copy params; new strike.').pxLT()
        4.227003911

        >>> s = Stock(S0=810, vol=.2, q=.02)
        >>> o = European(ref=s, right='call', K=800, T=.5, rf_r=.05, desc='53.39, Hull p.291')
        >>> o.pxLT(nsteps=3)  # option price from a 3-step tree (that's 2 time intervals)
        59.867529938

        >>> o.pxLT(nsteps=3, keep_hist=True)  # option price from a 3-step tree (that's 2 time intervals)
        59.867529938

        >>> o.px_spec.ref_tree  # prints reference tree  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        ((810.0,), (746.491768087...878.911232579...), (687.962913360...810.0..., 953.685129326...),
         (634.023026633...746.491768087...878.911232579...1034.8204598880159))

        >>> o.calc_px(method='LT', nsteps=2, keep_hist=True).px_spec.opt_tree
        ((53.39471637496134,), (5.062315192620067, 100.66143225703827), (0, 10.0, 189.3362341097378))

        >>> o.calc_px(method='LT', nsteps=2)   # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        European...px: 53.394716375...


        :Authors:
            Oleg Melnikov <xisreal@gmail.com>
        """

        return super().calc_px(method=method, nsteps=nsteps, npaths=npaths, keep_hist=keep_hist)

    def _calc_BS(self):
        """ Internal function for option valuation.

        See ``calc_px()`` for complete documentation.

        :Authors:
            Oleg Melnikov <xisreal@gmail.com>
        """

        _ = self
        d1 = (math.log(_.ref.S0 / _.K) + (_.rf_r + _.ref.vol ** 2 / 2.) * _.T)/(_.ref.vol * math.sqrt(_.T))
        d2 = d1 - _.ref.vol * math.sqrt(_.T)
        N = Util.norm_cdf

        # if calc of both prices is cheap, do both and include them into Price object.
        # Price.px should always point to the price of interest to the user
        # Save values as basic data types (int, floats, str), instead of np.array
        px_call = float(_.ref.S0 * math.exp(-_.ref.q * _.T) * N(d1) - _.K * math.exp(-_.rf_r * _.T) * N(d2))
        px_put = float(- _.ref.S0 * math.exp(-_.ref.q * _.T) * N(-d1) + _.K * math.exp(-_.rf_r * _.T) * N(-d2))
        px = px_call if _.signCP == 1 else px_put if _.signCP == -1 else None

        self.px_spec.add(px=px, sub_method='standard; Hull p.335', px_call=px_call, px_put=px_put, d1=d1, d2=d2)

        return self

    def _calc_LT(self):
        """ Internal function for option valuation.

        See ``calc_px()`` for complete documentation.

        :Authors:
            Oleg Melnikov <xisreal@gmail.com>
        """

        n = getattr(self.px_spec, 'nsteps', 3)
        _ = self.LT_specs(n)
        incr_n, decr_n = Vec(Util.arange(0, n + 1)), Vec(Util.arange(n, -1)) #Vectorized tuple. See util.py. 0..n; n..0.

        S = Vec(_['d'])**decr_n * Vec(_['u'])**incr_n * self.ref.S0
        O = ((S - self.K) * self.signCP ).max(0)
        S_tree, O_tree = None, None

        if getattr(self.px_spec, 'keep_hist', False):
            S_tree, O_tree = (S,), (O,)

            for i in range(n, 0, -1):
                O = (Vec(O[:i]) * (1 - _['p']) + Vec(O[1:]) * (_['p'])) * _['df_dt'] # prior option prices (@time step=i-1)
                S = Vec(S[1:i+1]) * _['d']                   # prior stock prices (@time step=i-1)
                S_tree, O_tree = (tuple(S),) + S_tree, (tuple(O),) + O_tree

            out = O_tree[0][0]
        else:
            csl = (0.,) + Vec(Util.cumsum(Util.log(Util.arange(1, n + 1))))         # logs avoid overflow & truncation
            tmp = Vec(csl[n]) - csl - tuple(reversed(csl)) + incr_n * math.log(_['p']) + decr_n * math.log(1 - _['p'])
            out = (sum(tmp.exp * _['df_T'] * tuple(O)))

        self.px_spec.add(px=float(out), sub_method='binary tree; Hull p.135', LT_specs=_, ref_tree=S_tree, opt_tree=O_tree)
        return self

    def _calc_MC(self):
        """ Internal function for option valuation.

        See ``calc_px()`` for complete documentation.

        :Authors:
            Oleg Melnikov <xisreal@gmail.com>
        """
        return self

    def _calc_FD(self):
        """ Internal function for option valuation.

        See ``calc_px()`` for complete documentation.

        :Authors:
            Oleg Melnikov <xisreal@gmail.com>
        """
        return self
