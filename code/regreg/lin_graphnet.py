import numpy as np

# Local imports

import subfunctions as sf
import updates
import l1smooth
from problems import linquadmodel


problem_statement=r"""
    lin_graphnet problem:
    Minimizes

    .. math::

       y^T\beta + \lambda_{1}\|\beta\|_{1} + \lambda_2 \|\beta\|_{2}^{2} + \lambda_3 \beta^T L \beta


    as a function of beta.
"""


class lin_graphnet(linquadmodel):

    __doc__ = problem_statement

    def initialize(self, data):
        """
        Generate initial tuple of arguments for update.
        """

        if len(data) == 2:
            self.Y = data[0]
            self.Lap = data[1]
            self.p = len(self.Y)
        else:
            raise ValueError("Data tuple not as expected")

        if hasattr(self,'initial_coefs'):
            self.set_coefs(self.initial_coefs)
        else:
            self.set_coefs(self.default_coefs)
            
    @property
    def default_penalties(self):
        """
        Default penalties for GraphNet
        """
        return np.zeros(1, np.dtype([(l, np.float) for l in ['l1', 'l2', 'l3']]))

    def obj(self, beta):
        beta = np.asarray(beta)
        return self.obj_smooth(beta) + self.obj_rough(beta)

    def obj_smooth(self, beta):
        #Smooth part of objective
        return -np.dot(self.Y, beta) + np.dot(beta,beta) * self.penalties['l2'] + np.dot(beta,np.dot(self.Lap,beta)) * self.penalties['l3']

    def obj_rough(self, beta):
        return np.sum(np.fabs(beta)) * self.penalties['l1'] 


class gengrad(lin_graphnet):
    
    def grad(self, beta):
        beta = np.asarray(beta)
        return -self.Y + 2*beta*self.penalties['l2'] + 2*np.dot(self.Lap,beta)*self.penalties['l3']

    def proximal(self, z, g, L):
        v = z - g / L
        return np.sign(v) * np.maximum(np.fabs(v)-self.penalties['l1']/L, 0)


class gengrad_nonneg(lin_graphnet):

    def grad(self, beta):
        beta = np.asarray(beta)
        return -self.Y + 2*beta*self.penalties['l2'] + 2*np.dot(self.Lap,beta)*self.penalties['l3']

    def proximal(self, z, g, L):
        v = z - g / L
        return (v >= 0) * np.maximum(np.fabs(v)-self.penalties['l1']/L, 0)

class lin_graphnet_sparse(lin_graphnet):
    
    #Assume Lap given as scipy.sparse matrix
    def obj_smooth(self, beta):
        beta = np.asarray(beta)
        return -np.dot(self.Y, beta) + np.dot(beta,beta) * self.penalties['l2'] + np.dot(beta,self.Lap.matvec(beta)) * self.penalties['l3']

class gengrad_sparse(lin_graphnet_sparse):
    
    def grad(self, beta):
        beta = np.asarray(beta)
        return -self.Y + 2*beta*self.penalties['l2'] + 2*self.Lap.matvec(beta)*self.penalties['l3']

    def proximal(self, z, g, L):
        v = z - g / L
        return np.sign(v) * np.maximum(np.fabs(v)-self.penalties['l1']/L, 0)


class gengrad_nonneg_sparse(lin_graphnet_sparse):
    
    def grad(self, beta):
        beta = np.asarray(beta)
        return -self.Y + 2*beta*self.penalties['l2'] + 2*self.Lap.matvec(beta)*self.penalties['l3']

    def proximal(self, z, g, L):
        v = z - g / L
        return (v >= 0) * np.maximum(np.fabs(v)-self.penalties['l1']/L, 0)

         

"""
class gengrad_smooth(gengrad):

    def smooth(self, L, epsilon):
        return l1smooth.l1smooth(self.grad, L, epsilon, l1=self.penalties['l1'], f=self.obj)


class cwpath(lasso):

    def __init__(self, data, penalties={}, initial_coefs=None):
        lasso.__init__(self, data, penalties=penalties,
                       initial_coefs=initial_coefs)

    # Differences to the standard initialization
        
    def initialize(self, data):
        lasso.initialize(self, data)
        self._ssq = sf.col_ssq(self.X)

    # Residuals must be updated if coefs change

    def set_coefs(self, coefs):
        self._coefs = coefs
        self.update_residuals()

    def get_coefs(self):
        if not hasattr(self, "_coefs"):
            self._coefs = self.default_coefs
        return self._coefs
    coefs = property(get_coefs, set_coefs)

    def update_residuals(self):
        self.r = self.Y - np.dot(self.X,self.coefs)

    # Inner products also must be updated if inner response changes
    def set_response(self,Y):
        self._Y = Y
        self.update_residuals()
        self.inner = sf.col_inner(self.X,self._Y)

    def get_response(self):
        return self._Y
    Y = property(get_response, set_response)

    def update_cwpath(self,
                      active,
                      nonzero,
                      inner_its = 1,
                      permute = False,
                      update_nonzero = False):
   
      
        if permute:
            active = np.random.permutation(active)
        if len(active):
            updates._update_lasso_cwpath(active,
                                         self.penalties,
                                         nonzero,
                                         self.coefs,
                                         self.r,
                                         self.X,
                                         self._ssq,
                                         inner_its,
                                         update_nonzero)

    def set_rowweights(self, weights):
        if weights is not None:
            self.rowwts = weights
            if self.update_resids:
                self.update_residuals()
            if hasattr(self,'_ssq'):
                self._ssq = sf.col_ssq(self.X,self.rowwts)

    def get_rowweights(self):
        if hasattr(self,'rowwts'):
            return self.rowwts.copy()
        else:
            return None
    rowweights = property(get_rowweights, set_rowweights)
"""