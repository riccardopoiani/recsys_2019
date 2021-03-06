import cProfile, pstats, io

from numpy.random import seed

from src.data_management.New_DataSplitter_leave_k_out import New_DataSplitter_leave_k_out
from src.data_management.RecSys2019Reader import RecSys2019Reader
from course_lib.Data_manager.DataSplitter_k_fold import DataSplitter_Warm_k_fold
from course_lib.KNN.UserKNNCFRecommender import UserKNNCFRecommender
from course_lib.KNN.ItemKNNCFRecommender import ItemKNNCFRecommender
from src.data_management.RecSys2019Reader_utils import merge_UCM
from src.data_management.data_getter import get_warmer_UCM
from src.model.HybridRecommender.HybridRankBasedRecommender import HybridRankBasedRecommender
import numpy as np

from src.model.KNN.UserSimilarityRecommender import UserSimilarityRecommender

SEED = 69420

if __name__ == '__main__':
    seed(SEED)

    # Data loading
    data_reader = RecSys2019Reader("../../data/")
    data_reader = New_DataSplitter_leave_k_out(data_reader, k_out_value=3, use_validation_set=False,
                                               force_new_split=True)
    data_reader.load_data()
    URM_train, URM_test = data_reader.get_holdout_split()
    URM_all = data_reader.dataReader_object.get_URM_all()
    UCM_age = data_reader.dataReader_object.get_UCM_from_name("UCM_age")
    UCM_region = data_reader.dataReader_object.get_UCM_from_name("UCM_region")
    UCM_all, _ = merge_UCM(UCM_age, UCM_region, {}, {})

    UCM_all = get_warmer_UCM(UCM_all, URM_all, threshold_users=3)
    UCM_all, _ = merge_UCM(UCM_all, URM_train, {}, {})

    warm_users_mask = np.ediff1d(URM_train.tocsr().indptr) > 0
    warm_users = np.arange(URM_train.shape[0])[warm_users_mask]

    # Reset seed for hyper-parameter tuning
    seed()

    item_cf_keywargs = {'topK': 5, 'shrink': 1000, 'similarity': 'cosine', 'normalize': True,
                        'feature_weighting': 'TF-IDF'}
    item_cf = ItemKNNCFRecommender(URM_train)
    item_cf.fit(**item_cf_keywargs)

    kwargs = {'topK': 100, 'shrink': 0, 'similarity': 'cosine', 'normalize': False}
    model = UserSimilarityRecommender(URM_train, UCM_all, item_cf)
    model.fit(**kwargs)
    pr = cProfile.Profile()
    pr.enable()

    for user in range(1000):
        model.recommend(user, cutoff=10)

    pr.disable()
    s = io.StringIO()
    sortby = "cumulative"
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())
