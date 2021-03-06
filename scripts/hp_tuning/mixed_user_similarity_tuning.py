from datetime import datetime

import numpy as np

from course_lib.Base.Evaluation.Evaluator import EvaluatorHoldout
from src.data_management.New_DataSplitter_leave_k_out import New_DataSplitter_leave_k_out
from src.data_management.RecSys2019Reader import RecSys2019Reader
from src.data_management.data_reader import get_UCM_train
from src.model import new_best_models
from src.model.HybridRecommender.HybridMixedSimilarityRecommender import UserHybridModelRecommender
from src.tuning.holdout_validation.run_parameter_search_hybrid_mixed_similarity import run_parameter_search_mixed_similarity_user
from src.utils.general_utility_functions import get_split_seed

if __name__ == '__main__':
    # Data loading
    root_data_path = "../../data/"
    data_reader = RecSys2019Reader(root_data_path)
    data_reader = New_DataSplitter_leave_k_out(data_reader, k_out_value=3, use_validation_set=False,
                                               force_new_split=True, seed=get_split_seed())
    data_reader.load_data()
    URM_train, URM_test = data_reader.get_holdout_split()

    # Build UCMs
    UCM_all = get_UCM_train(data_reader)

    # Setting evaluator
    cold_users_mask = np.ediff1d(URM_train.tocsr().indptr) == 0
    cold_users = np.arange(URM_train.shape[0])[cold_users_mask]

    cutoff_list = [10]
    evaluator_test = EvaluatorHoldout(URM_test, cutoff_list=[10], ignore_users=cold_users)

    # Path setting
    print("Start tuning...")
    version_path = "../../report/hp_tuning/mixed_user/"
    now = datetime.now().strftime('%b%d_%H-%M-%S')
    now = now + "_k_out_value_3_eval/"
    version_path = version_path + now

    user_cf = new_best_models.UserCF.get_model(URM_train=URM_train, load_model=False, save_model=False)
    user_cbf = new_best_models.UserCBF_CF_Warm.get_model(URM_train=URM_train, UCM_train=UCM_all)

    hybrid = UserHybridModelRecommender(URM_train)
    hybrid.add_similarity_matrix(user_cf.W_sparse)
    hybrid.add_similarity_matrix(user_cbf.W_sparse)

    run_parameter_search_mixed_similarity_user(hybrid, URM_train=URM_train, output_folder_path=version_path,
                                               evaluator_validation=evaluator_test, evaluator_test=None,
                                               n_cases=50, n_random_starts=15, metric_to_optimize="MAP")

    print("...tuning ended")
