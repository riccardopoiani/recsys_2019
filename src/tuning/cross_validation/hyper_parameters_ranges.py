from skopt.space import Integer, Real, Categorical

from course_lib.FeatureWeighting.CFW_D_Similarity_Linalg import CFW_D_Similarity_Linalg
from course_lib.GraphBased.P3alphaRecommender import P3alphaRecommender
from course_lib.GraphBased.RP3betaRecommender import RP3betaRecommender
from course_lib.KNN.ItemKNNCBFRecommender import ItemKNNCBFRecommender
from course_lib.KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from course_lib.KNN.UserKNNCFRecommender import UserKNNCFRecommender
from course_lib.MatrixFactorization.PureSVDRecommender import PureSVDRecommender
from course_lib.SLIM_BPR.Cython.SLIM_BPR_Cython import SLIM_BPR_Cython
from src.model.FactorizationMachine.FieldAwareFMRecommender import FieldAwareFMRecommender
from src.model.KNN.ItemKNNDotCFRecommender import ItemKNNDotCFRecommender
from src.model.KNN.ItemKNNCBFCFRecommender import ItemKNNCBFCFRecommender
from src.model.KNN.NewItemKNNCBFRecommender import NewItemKNNCBFRecommender
from src.model.KNN.NewUserKNNCFRecommender import NewUserKNNCFRecommender
from src.model.KNN.UserKNNCBFCFRecommender import UserKNNCBFCFRecommender
from src.model.KNN.UserKNNCBFRecommender import UserKNNCBFRecommender
from src.model.KNN.UserKNNDotCFRecommender import UserKNNDotCFRecommender
from src.model.MatrixFactorization.FunkSVDRecommender import FunkSVDRecommender
from src.model.MatrixFactorization.ImplicitALSRecommender import ImplicitALSRecommender
from src.model.MatrixFactorization.LightFMRecommender import LightFMRecommender
from src.model.MatrixFactorization.LogisticMFRecommender import LogisticMFRecommender
from src.model.MatrixFactorization.MF_BPR_Recommender import MF_BPR_Recommender
from src.model.MatrixFactorization.NewPureSVDRecommender import NewPureSVDRecommender

# ------------------------- HYPER PARAMETERS RANGE ------------------------- #
from src.model.SLIM.SSLIM_BPR import SSLIM_BPR

HYPER_PARAMETERS_RANGE = {

    CFW_D_Similarity_Linalg.RECOMMENDER_NAME: {
        "topK": Integer(2, 2000),
        "add_zeros_quota": Real(low=0, high=0.1, prior='uniform'),
        "normalize_similarity": Categorical([True, False])
    },

    # ------ Matrix Factorization ------ #
    ImplicitALSRecommender.RECOMMENDER_NAME: {
        "num_factors": Integer(300, 550),
        "regularization": Real(low=1e-2, high=200, prior='log-uniform'),
        "epochs": Categorical([50]),
        "confidence_scaling": Categorical(["linear"]),
        "alpha": Real(low=1e-2, high=1e2, prior='log-uniform')
    },

    MF_BPR_Recommender.RECOMMENDER_NAME: {
        "num_factors": Categorical([600]),
        "regularization": Real(low=1e-4, high=1e-1, prior='log-uniform'),
        "learning_rate": Real(low=1e-2, high=1e-1, prior='log-uniform'),
        "epochs": Categorical([300])
    },

    FunkSVDRecommender.RECOMMENDER_NAME: {
        "num_factors": Integer(50, 400),
        "regularization": Real(low=1e-5, high=1e-0, prior='log-uniform'),
        "learning_rate": Real(low=1e-2, high=1e-1, prior='log-uniform'),
        "epochs": Categorical([500])
    },

    LogisticMFRecommender.RECOMMENDER_NAME: {
        "num_factors": Integer(20, 400),
        "regularization": Real(low=1e-5, high=1e1, prior='log-uniform'),
        "learning_rate": Real(low=1e-2, high=1e-1, prior='log-uniform'),
        "epochs": Categorical([300])
    },

    LightFMRecommender.RECOMMENDER_NAME: {
        'no_components': Categorical([100]),
        'epochs': Categorical([100])
    },

    FieldAwareFMRecommender.RECOMMENDER_NAME: {
        'epochs': Categorical([200]),
        'latent_factors': Integer(low=20, high=500),
        'regularization': Real(low=10e-7, high=10e-1, prior="log-uniform"),
        'learning_rate': Real(low=10e-3, high=10e-1, prior="log-uniform")
    },

    PureSVDRecommender.RECOMMENDER_NAME: {
        "num_factors": Integer(10, 1000),
    },

    NewPureSVDRecommender.RECOMMENDER_NAME: {
        "num_factors": Integer(500, 1000),
        "n_oversamples": Integer(10, 50),
        "n_iter": Integer(10, 50),
        "feature_weighting": Categorical(["none", "BM25", "TF-IDF"])
    },

    # ------ Collaborative KNN Method ------ #
    ItemKNNCFRecommender.RECOMMENDER_NAME: {
        "topK": Integer(1, 1000),
        "shrink": Integer(0, 2000),
        "normalize": Categorical([True, False])
    },
    UserKNNCFRecommender.RECOMMENDER_NAME: {
        "topK": Integer(1, 3000),
        "shrink": Integer(0, 2000),
        "normalize": Categorical([True, False])
    },
    NewUserKNNCFRecommender.RECOMMENDER_NAME: {
        "topK": Integer(1, 3000),
        "shrink": Integer(0, 2000),
        "normalize": Categorical([True, False])
    },
    UserKNNDotCFRecommender.RECOMMENDER_NAME: {
        "topK": Integer(1, 3000),
        "shrink": Integer(0, 2000),
        "normalize": Categorical([True, False]),
        "feature_weighting": Categorical(["none", "BM25", "TF-IDF"])
    },
    ItemKNNDotCFRecommender.RECOMMENDER_NAME: {
        "topK": Integer(3, 30),
        "shrink": Integer(0, 2000),
        "normalize": Categorical([True, False]),
        "feature_weighting": Categorical(["none", "BM25", "TF-IDF"])
    },

    # ------ Content KNN Method ------ #
    ItemKNNCBFRecommender.RECOMMENDER_NAME: {
        "topK": Integer(1, 1000),
        "shrink": Integer(0, 2000),
        "normalize": Categorical([True, False]),
        # "interactions_feature_weighting": Categorical(["none", "BM25", "TF-IDF"])
    },
    NewItemKNNCBFRecommender.RECOMMENDER_NAME: {
        "topK": Integer(1, 1000),
        "shrink": Integer(0, 2000),
        "normalize": Categorical([True, False]),
        "interactions_feature_weighting": Categorical(["none", "BM25", "TF-IDF"])
    },
    ItemKNNCBFCFRecommender.RECOMMENDER_NAME: {
        "topK": Integer(1, 200),
        "shrink": Integer(0, 2000),
        "normalize": Categorical([True, False]),
        "interactions_feature_weighting": Categorical(["none", "BM25", "TF-IDF"])
    },

    # ------ Demographic KNN Method ------ #
    UserKNNCBFRecommender.RECOMMENDER_NAME: {
        "topK": Integer(5, 3000),
        "shrink": Integer(0, 2000),
        "normalize": Categorical([True, False]),
        "interactions_feature_weighting": Categorical(["none", "BM25", "TF-IDF"])
    },
    UserKNNCBFCFRecommender.RECOMMENDER_NAME: {
        "topK": Integer(5, 4000),
        "shrink": Integer(0, 2000),
        "normalize": Categorical([True, False]),
        "interactions_feature_weighting": Categorical(["none", "BM25", "TF-IDF"])
    },

    # ------ ML Item Similarity Based Method ------ #
    P3alphaRecommender.RECOMMENDER_NAME: {
        "topK": Integer(1, 1000),
        "alpha": Real(low=0, high=2, prior='uniform'),
        "normalize_similarity": Categorical([True, False])
    },

    RP3betaRecommender.RECOMMENDER_NAME: {
        "topK": Integer(1, 1000),
        "alpha": Real(low=0, high=2, prior='uniform'),
        "beta": Real(low=0, high=2, prior='uniform'),
        "normalize_similarity": Categorical([True, False])
    },
    SLIM_BPR_Cython.RECOMMENDER_NAME: {
        "topK": Integer(5, 1000),
        "epochs": Categorical([1000, 1100, 1200, 1300, 1400, 1500, 1600]),
        "symmetric": Categorical([True, False]),
        "sgd_mode": Categorical(["adagrad", "adam"]),
        "lambda_i": Real(low=1e-12, high=1e-1, prior='log-uniform'),
        "lambda_j": Real(low=1e-12, high=1e-1, prior='log-uniform'),
        "learning_rate": Real(low=1e-8, high=1e-4, prior='log-uniform')
    },
    SSLIM_BPR.RECOMMENDER_NAME: {
        "topK": Integer(5, 100),
        "epochs": Categorical([1200, 1500, 1700]),
        "symmetric": Categorical([True, False]),
        "sgd_mode": Categorical(["adam"]),
        "lambda_i": Real(low=1e-12, high=1e-1, prior='log-uniform'),
        "lambda_j": Real(low=1e-12, high=1e-1, prior='log-uniform'),
        "learning_rate": Real(low=1e-8, high=1e-4, prior='log-uniform'),
        "alpha": Real(low=0.01, high=0.99, prior='log-uniform')
    }

}


def get_hyper_parameters_dictionary(recommender_class):
    return HYPER_PARAMETERS_RANGE[recommender_class.RECOMMENDER_NAME]


def add_knn_similarity_type_hyper_parameters(hyper_parameters_dictionary: dict, similarity_type: str,
                                             allow_weighting=True):
    hyper_parameters_dictionary["similarity"] = Categorical([similarity_type])
    is_set_similarity = similarity_type in ["tversky", "dice", "jaccard", "tanimoto"]

    if similarity_type == "asymmetric":
        hyper_parameters_dictionary["asymmetric_alpha"] = Real(low=0, high=2, prior='uniform')
        hyper_parameters_dictionary["normalize"] = Categorical([True])

    elif similarity_type == "tversky":
        hyper_parameters_dictionary["tversky_alpha"] = Real(low=0, high=2, prior='uniform')
        hyper_parameters_dictionary["tversky_beta"] = Real(low=0, high=2, prior='uniform')
        hyper_parameters_dictionary["normalize"] = Categorical([True])

    elif similarity_type == "euclidean":
        hyper_parameters_dictionary["normalize"] = Categorical([True, False])
        hyper_parameters_dictionary["normalize_avg_row"] = Categorical([True, False])
        hyper_parameters_dictionary["similarity_from_distance_mode"] = Categorical(["lin", "log", "exp"])

    if not is_set_similarity:
        if allow_weighting:
            hyper_parameters_dictionary["feature_weighting"] = Categorical(["none", "BM25", "TF-IDF"])
    return hyper_parameters_dictionary
