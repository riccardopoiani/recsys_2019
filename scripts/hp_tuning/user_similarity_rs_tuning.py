from datetime import datetime

from course_lib.Base.Evaluation.Evaluator import *
from src.data_management.New_DataSplitter_leave_k_out import *
from src.data_management.RecSys2019Reader import RecSys2019Reader
from src.data_management.data_reader import get_ICM_train, get_UCM_train
from src.model import new_best_models
from src.model.KNN.UserSimilarityRecommender import UserSimilarityRecommender
from src.tuning.holdout_validation.run_parameter_search_user_similarity_rs import run_parameter_search_user_similarity_rs
from src.utils.general_utility_functions import get_split_seed

if __name__ == '__main__':
    # Data loading
    root_data_path = "../../data/"
    data_reader = RecSys2019Reader(root_data_path)
    data_reader = New_DataSplitter_leave_k_out(data_reader, k_out_value=3, use_validation_set=False,
                                               force_new_split=True, seed=get_split_seed())
    data_reader.load_data()
    URM_train, URM_test = data_reader.get_holdout_split()

    # Build ICMs
    ICM_all = get_ICM_train(data_reader)

    # Build UCMs
    UCM_all = get_UCM_train(data_reader)

    warm_users_mask = np.ediff1d(URM_train.tocsr().indptr) > 0
    warm_users = np.arange(URM_train.shape[0])[warm_users_mask]

    best_model = new_best_models.ItemCBF_CF.get_model(URM_train, ICM_train=ICM_all)

    # Setting evaluator
    cutoff_list = [10]
    evaluator = EvaluatorHoldout(URM_test, cutoff_list=cutoff_list, ignore_users=warm_users)

    version_path = "../../report/hp_tuning/user_similarity_rs/"
    now = datetime.now().strftime('%b%d_%H-%M-%S')
    now = now + "_k_out_value_3/"
    version_path = version_path + "/" + now

    run_parameter_search_user_similarity_rs(UserSimilarityRecommender, best_model, URM_train, UCM_all,
                                            UCM_name="UCM_all",
                                            metric_to_optimize="MAP",
                                            evaluator_validation=evaluator,
                                            output_folder_path=version_path,
                                            parallelizeKNN=True,
                                            n_cases=60, n_random_starts=20)
    print("...tuning ended")
