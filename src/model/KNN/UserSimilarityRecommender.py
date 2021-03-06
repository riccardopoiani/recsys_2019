from course_lib.Base.BaseRecommender import BaseRecommender
from course_lib.Base.Recommender_utils import check_matrix, similarityMatrixTopK
from course_lib.Base.BaseSimilarityMatrixRecommender import BaseSimilarityMatrixRecommender
from course_lib.Base.IR_feature_weighting import okapi_BM_25, TF_IDF
import numpy as np
import scipy.sparse as sps

from course_lib.Base.Similarity.Compute_Similarity import Compute_Similarity


class UserSimilarityRecommender(BaseSimilarityMatrixRecommender):
    """ UserKNN Similarity Recommender"""

    RECOMMENDER_NAME = "UserSimilarityRecommender"

    FEATURE_WEIGHTING_VALUES = ["BM25", "TF-IDF", "none"]

    def __init__(self, URM_train, UCM_train, recommender: BaseRecommender, verbose=True):
        super(UserSimilarityRecommender, self).__init__(URM_train, verbose=verbose)

        cold_users_mask = np.ediff1d(URM_train.tocsr().indptr) == 0
        self.cold_users = np.arange(URM_train.shape[0])[cold_users_mask]
        self.UCM_train = sps.hstack([UCM_train, URM_train], format="csr")
        self.recommender = recommender

    def fit(self, topK=50, shrink=100, similarity='cosine', normalize=True, feature_weighting="none",
            **similarity_args):

        self.topK = topK
        self.topComputeK = topK + len(self.cold_users)
        self.shrink = shrink

        if feature_weighting not in self.FEATURE_WEIGHTING_VALUES:
            raise ValueError(
                "Value for 'feature_weighting' not recognized. Acceptable values are {}, provided was '{}'".format(
                    self.FEATURE_WEIGHTING_VALUES, feature_weighting))

        if feature_weighting == "BM25":
            self.UCM_train = self.UCM_train.astype(np.float32)
            self.UCM_train = okapi_BM_25(self.UCM_train)

        elif feature_weighting == "TF-IDF":
            self.UCM_train = self.UCM_train.astype(np.float32)
            self.UCM_train = TF_IDF(self.UCM_train)

        similarity = Compute_Similarity(self.UCM_train.T, shrink=shrink, topK=self.topComputeK, normalize=normalize,
                                        similarity=similarity, **similarity_args)

        self.W_sparse = similarity.compute_similarity()
        self.W_sparse = self.W_sparse.tocsc()

        for user in self.cold_users:
            self.W_sparse.data[self.W_sparse.indptr[user]: self.W_sparse.indptr[user+1]] = 0

        self.W_sparse.eliminate_zeros()
        self.W_sparse = self.W_sparse.tocsr()

        self.W_sparse = similarityMatrixTopK(self.W_sparse, k=self.topK).tocsr()
        self.W_sparse = check_matrix(self.W_sparse, format='csr')

        # Add identity matrix to the recommender
        self.recommender.W_sparse = self.recommender.W_sparse + sps.identity(self.recommender.W_sparse.shape[0],
                                                                             format="csr")

    def _compute_item_score(self, user_id_array, items_to_compute=None):
        """
        URM_train and W_sparse must have the same format, CSR
        :param user_id_array:
        :param items_to_compute: not implemented!!
        :return:
        """

        self._check_format()

        def calculate_scores(user):
            user = user[0]
            user_weights = self.W_sparse.data[self.W_sparse.indptr[user]:self.W_sparse.indptr[user + 1]]

            significant_users = self.W_sparse.indices[self.W_sparse.indptr[user]: self.W_sparse.indptr[user + 1]]

            scores = self.recommender._compute_item_score(significant_users, items_to_compute=None)

            weighted_scores = np.multiply(scores, np.reshape(user_weights, newshape=(len(user_weights), 1)))
            return np.sum(weighted_scores, axis=0)

        item_scores = np.apply_along_axis(calculate_scores, 1, np.reshape(user_id_array,
                                                                          newshape=(len(user_id_array), 1)))

        return np.array(item_scores).reshape(len(user_id_array), self.n_items)

