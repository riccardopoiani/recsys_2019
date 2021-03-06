from abc import ABC

import numpy as np
import scipy.sparse as sps
from tqdm import tqdm

from course_lib.Base.BaseRecommender import BaseRecommender
from course_lib.Base.BaseSimilarityMatrixRecommender import BaseItemSimilarityMatrixRecommender, \
    BaseUserSimilarityMatrixRecommender
from course_lib.Base.Recommender_utils import similarityMatrixTopK
from course_lib.GraphBased.P3alphaRecommender import P3alphaRecommender
from course_lib.GraphBased.RP3betaRecommender import RP3betaRecommender
from course_lib.KNN.ItemKNNCBFRecommender import ItemKNNCBFRecommender
from course_lib.KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from course_lib.KNN.UserKNNCFRecommender import UserKNNCFRecommender
from course_lib.SLIM_BPR.Cython.SLIM_BPR_Cython import SLIM_BPR_Cython
from src.model.Ensemble.BaggingUtils import get_user_bootstrap, get_item_bootstrap
from src.model.KNN.ItemKNNCBFCFRecommender import ItemKNNCBFCFRecommender
from src.model.KNN.ItemKNNDotCFRecommender import ItemKNNDotCFRecommender
from src.model.KNN.UserKNNCBFCFRecommender import UserKNNCBFCFRecommender
from src.model.KNN.UserKNNCBFRecommender import UserKNNCBFRecommender
from src.utils.general_utility_functions import block_print, enable_print, get_split_seed


class BaggingMergeRecommender(BaseRecommender, ABC):
    COMPATIBLE_RECOMMENDERS = []

    def __init__(self, URM_train, recommender_class, do_bootstrap=True, weight_replacement=True,
                 **recommender_constr_kwargs):
        if not (recommender_class in self.COMPATIBLE_RECOMMENDERS):
            raise ValueError("The only compatible recommenders are: {}".format(self.COMPATIBLE_RECOMMENDERS))

        super().__init__(URM_train)
        self.weight_replacement = weight_replacement
        self.do_bootstrap = do_bootstrap
        self.recommender_class = recommender_class
        self.recommender_kwargs = recommender_constr_kwargs

    # TODO CHANGE SEED
    def fit(self, num_models=5, hyper_parameters_range=None, seed=876133, **kwargs):
        """
        Fit all the num_models and merge them into a unique model

        :param num_models: number of models in the bagging recommender
        :param hyper_parameters_range: hyper parameters range to give some more diversity in models
        :param seed:
        """
        if hyper_parameters_range is None:
            hyper_parameters_range = {}

        np.random.seed(seed)
        seeds = np.random.randint(low=0, high=2**16-1, size=num_models)

        for i in tqdm(range(num_models), desc="Fitting bagging models"):
            URM_bootstrap = self.URM_train
            recommender_kwargs = self.recommender_kwargs.copy()
            if self.do_bootstrap:
                URM_bootstrap, users_added = get_user_bootstrap(self.URM_train, seeds[i])

            parameters = {}
            for parameter_name, parameter_range in hyper_parameters_range.items():
                parameters[parameter_name] = parameter_range.rvs(random_state=seeds[i])

                # Deals with array since .rvs() does not return always a scalar
                if type(parameters[parameter_name]) is np.ndarray:
                    parameters[parameter_name] = parameters[parameter_name][0]

            block_print()
            recommender_object = self.recommender_class(URM_bootstrap, **recommender_kwargs)
            recommender_object.fit(**parameters)
            enable_print()

            self._update_model(recommender_object)
        np.random.seed()  # Re-set random seed for following computations
        self._reconcile_model(num_models)

    def _update_model(self, recommender_object):
        """
        Update the model with the recommender system fitted
        :param recommender_object: a recommender system fitted
        """
        raise NotImplementedError("The method is not implemented in this class")

    def _reconcile_model(self, num_models):
        """
        Reconcile the model after updating the model (e.g. averaging, apply KNN, ...)
        """
        raise NotImplementedError("The method is not implemented in this class")


class BaggingMergeItemSimilarityRecommender(BaggingMergeRecommender, BaseItemSimilarityMatrixRecommender):
    """
    Bagging Merge Item Similarity Recommender: samples with replacement only the positive interactions and groups
    the model by merging them
    """

    RECOMMENDER_NAME = "BaggingMergeItemSimilarityRecommender"

    COMPATIBLE_RECOMMENDERS = [ItemKNNCBFRecommender, ItemKNNCBFCFRecommender, ItemKNNCFRecommender,
                               SLIM_BPR_Cython, P3alphaRecommender, RP3betaRecommender,
                               ItemKNNDotCFRecommender]

    def __init__(self, URM_train, recommender_class, do_bootstrap=True, weight_replacement=True,
                 **recommender_constr_kwargs):
        super().__init__(URM_train, recommender_class, do_bootstrap, weight_replacement,
                         **recommender_constr_kwargs)

        self.W_sparse = None

    def fit(self, topK=-1, num_models=5, hyper_parameters_range=None, seed=get_split_seed()):
        self.topK = topK
        super().fit(num_models, hyper_parameters_range, seed=seed)

    def _update_model(self, recommender_object):
        if self.W_sparse is None:
            self.W_sparse = recommender_object.W_sparse[:self.n_items, :self.n_items]
        else:
            self.W_sparse = self.W_sparse + recommender_object.W_sparse[:self.n_items, :self.n_items]

    def _reconcile_model(self, num_models):
        self.W_sparse = self.W_sparse / num_models
        if self.topK >= 0:
            self.W_sparse = similarityMatrixTopK(self.W_sparse, k=self.topK).tocsr()


class BaggingMergeUserSimilarityRecommender(BaggingMergeRecommender, BaseUserSimilarityMatrixRecommender):
    """
    Bagging Merge User Similarity Recommender: samples with replacement only the positive interactions and
    groups the model by merging them
    """

    RECOMMENDER_NAME = "BaggingMergeUserSimilarityRecommender"

    COMPATIBLE_RECOMMENDERS = [UserKNNCBFRecommender, UserKNNCFRecommender, UserKNNCBFCFRecommender]

    def __init__(self, URM_train, recommender_class, do_bootstrap=True, weight_replacement=True,
                 **recommender_constr_kwargs):
        super().__init__(URM_train, recommender_class, do_bootstrap, weight_replacement,
                         **recommender_constr_kwargs)
        self.W_sparse = None

    def fit(self, topK=-1, num_models=5, hyper_parameters_range=None, seed=get_split_seed()):
        self.topK = topK
        super().fit(num_models, hyper_parameters_range, seed=seed)

    def _update_model(self, recommender_object):
        if self.W_sparse is None:
            self.W_sparse = recommender_object.W_sparse[:self.n_users, :self.n_users]
        else:
            self.W_sparse = self.W_sparse + recommender_object.W_sparse[:self.n_users, :self.n_users]

    def _reconcile_model(self, num_models):
        self.W_sparse = self.W_sparse / num_models

        if self.topK >= 0:
            self.W_sparse = similarityMatrixTopK(self.W_sparse, k=self.topK).tocsr()
