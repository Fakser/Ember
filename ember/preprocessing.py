from sklearn.pipeline import Pipeline, FeatureUnion, make_pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, LabelEncoder
import numpy as np
import pandas as pd
from category_encoders import TargetEncoder, LeaveOneOutEncoder, WOEEncoder

class Preprocessor:


    def __init__(self):
        self.branches = {}  
        self.pipes = {}
        self.union = None
        self.pipeline = None


    def add_branch(self, name):
        self.branches[name] = []

    def add_transformer_to_branch(self, name, transformer):
        if name in list(self.branches.keys()):
            self.branches[name].append(transformer)
        else:
            self.branches[name] = [transformer]

    def merge(self):
        for branch in self.branches.keys():
            self.pipes[branch] = make_pipeline(*self.branches[branch])
        self.union = FeatureUnion([(pipe_name, self.pipes[pipe_name]) for pipe_name in self.pipes.keys()])

        return self.union


class GeneralScaler(BaseEstimator, TransformerMixin):
    """

        TODO: ADD MORE SCALERS

    """

    def __init__(self, kind):

        if kind == 'SS':
            self.scaler = StandardScaler()
        elif kind == 'MMS':
            self.scaler = MinMaxScaler()
        else:
            raise Exception("No such kind of scaler supported! \n Supported kinds: SS MMS")

    def fit(self, X, y=None):

        self.scaler.fit(X)
        return self

    def transform(self, X, y=None):

        return self.scaler.transform(X)


class MultiColumnTransformer(BaseEstimator, TransformerMixin):

    """

        Uogolnienie transformatorow dla wielu kolumn jesli potrafią zadzialac tylko na jedną, jak np. label encoder

    """

    def __init__(self, transformer, match_col_names = False, **kwargs):
        self.transformer = transformer
        self.kwargs = kwargs
        self.match_col_names = match_col_names
        self.transformers = []
        self.columns = []

    def __getitem__(self, index):
        return self.transformers[index]


    def fit(self, X, y = None):
        """
            Jesli podajemy numpy array to w przypadku podania jednej kolumny, array musi być w postanci (-1,1) - tzn. dwuwymiarowy

        """
        if isinstance(X, pd.DataFrame):
            self.columns =  list(X.columns)
        elif isinstance(X, np.ndarray):
            if len(X.shape) == 2:
                self.columns = list(range(X.shape[1]))
                X = pd.DataFrame(X)
            else:
                raise Exception("Unsupported data structure. Provided structure should be two-dimentional. In case if your data is single column reshape it to (-1,1)")

        else:
            raise Exception("Unsupported data structure. Use pandas dataframe or 2-dim numpy array instea")

        self.transformers = [self.transformer(**self.kwargs) for i in range(len(self.columns))]


        for i in range(len(self.columns)):
            self.transformers[i].fit(X.iloc[:, i].astype(str))


        return self
    
    def transform(self, X, y = None):

        if isinstance(X, pd.DataFrame):
            if self.match_col_names and self.columns != list(X.columns):
                raise Exception("Invalid column names structure")
            X = X.to_numpy().reshape(-1,len(self.columns))
        elif isinstance(X, np.ndarray):
            if len(X.shape) == 2:
                if len(self.columns) != X.shape[1]:
                    raise Exception("Number of columns don't match with fit")
            else:
                raise Exception("Unsupported data structure. Provided structure should be two-dimentional. In case if your data is single column reshape it to (-1,1)")

        else:
            raise Exception("Unsupported data structure")

        final = None

        for i in range(len(self.columns)):
            result = self.transformers[i].transform(X[:, i])
            if not isinstance(result, np.ndarray):
                raise Exception("One of transformers returned {} instead of {}".format(type(result), np.ndarray))
            if len(result.shape) > 2:
                raise Exception("One of transformers returned over 2-dim ndarray ")
            if len(result.shape) == 1:
                result = result.reshape(-1,1)
            if not isinstance(final, np.ndarray):
                final = result
            else:
                final = np.concatenate((final, result), axis = 1)    


        return final




class GeneralEncoder(BaseEstimator, TransformerMixin):

    """
        Do implementacji:

        Label Encoding
        One-Hot encoding
        Target encoding
        Leave-one-out encoding
        Weight of Evidence


    """



    def __init__(self, kind, **kwargs):
        self.kind = kind
        if kind not in ['OHE','TE','LOOE','WOE', 'LE']:
            raise Exception("Encoder type not supported, choose one of ('OHE','TE','LOOE','WOE', 'LE')")
        else:
            if kind == 'OHE':
                self.encoder = OneHotEncoder(**kwargs)
            elif kind == 'TE':
                self.encoder = TargetEncoder(**kwargs)
            elif kind == 'LOOE':
                self.encoder = LeaveOneOutEncoder(**kwargs)
            elif kind == 'WOE':
                self.encoder = WOEEncoder(**kwargs)
            elif kind == 'LE':
                self.encoder = MultiColumnTransformer(LabelEncoder)

    def fit(self, X, y = None):
        if isinstance(self.encoder, OneHotEncoder):
            self.encoder.fit(X)
        else:
            self.encoder.fit(X,y)

        return self

    def transform(self, X, y = None):
        return self.encoder.transform(X)


