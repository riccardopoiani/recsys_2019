from datetime import datetime

from course_lib.Base.Evaluation.Evaluator import *
from src.data_management.New_DataSplitter_leave_k_out import *
from src.data_management.RecSys2019Reader import RecSys2019Reader
from src.data_management.data_reader import get_ICM_train, get_UCM_train, get_ignore_users
from src.model import best_models_lower_threshold_23, new_best_models
from src.model.HybridRecommender.HybridWeightedAverageRecommender import HybridWeightedAverageRecommender
from src.tuning.holdout_validation.run_parameter_search_hybrid import run_parameter_search_hybrid
from src.utils.general_utility_functions import get_split_seed

# PARAMETERS
K_OUT = 3
CUTOFF = 10
ALLOW_COLD_USERS = False
LOWER_THRESHOLD = 23  # Remove users below or equal this threshold (default value: -1)
UPPER_THRESHOLD = 2 ** 16 - 1  # Remove users above or equal this threshold (default value: 2**16-1)
IGNORE_NON_TARGET_USERS = True

# HYBRID PARAMETERS
NORMALIZE = True


def _get_all_models(URM_train, ICM_all, UCM_all):
    all_models = {}

    all_models['FUSION'] = best_models_lower_threshold_23.FusionMergeItem_CBF_CF.get_model(URM_train=URM_train,
                                                                                           ICM_train=ICM_all)
    all_models['ItemDotCF'] = best_models_lower_threshold_23.ItemDotCF.get_model(URM_train=URM_train)
    all_models['ItemCBF_CF'] = best_models_lower_threshold_23.ItemCBF_CF.get_model(URM_train=URM_train,
                                                                                   ICM_train=ICM_all)
    all_models['ItemCBF_FW'] = new_best_models.ItemCBF_all_FW.get_model(URM_train=URM_train,
                                                                        ICM_train=ICM_all)

    return all_models


if __name__ == '__main__':
    # Data loading
    root_data_path = "../../data/"
    data_reader = RecSys2019Reader(root_data_path)
    data_reader = New_DataSplitter_leave_k_out(data_reader, k_out_value=K_OUT, use_validation_set=False,
                                               force_new_split=True, seed=get_split_seed())
    data_reader.load_data()
    URM_train, URM_test = data_reader.get_holdout_split()

    # Build ICMs
    ICM_all = get_ICM_train(data_reader)

    # Build UCMs
    UCM_all = get_UCM_train(data_reader)

    model = HybridWeightedAverageRecommender(URM_train, normalize=NORMALIZE)

    all_models = _get_all_models(URM_train=URM_train, UCM_all=UCM_all, ICM_all=ICM_all)
    for model_name, model_object in all_models.items():
        model.add_fitted_model(model_name, model_object)
    print("The models added in the hybrid are: {}".format(list(all_models.keys())))

    # Setting evaluator
    ignore_users = get_ignore_users(URM_train, data_reader.get_original_user_id_to_index_mapper(),
                                    lower_threshold=LOWER_THRESHOLD, upper_threshold=UPPER_THRESHOLD,
                                    ignore_non_target_users=IGNORE_NON_TARGET_USERS)

    evaluator = EvaluatorHoldout(URM_test, cutoff_list=[CUTOFF], ignore_users=ignore_users)

    version_path = "../../report/hp_tuning/hybrid_weighted_avg"
    now = datetime.now().strftime('%b%d_%H-%M-%S')
    now = now + "_k_out_value_{}/".format(K_OUT)
    version_path = version_path + "/" + now

    run_parameter_search_hybrid(model, metric_to_optimize="MAP",
                                evaluator_validation=evaluator,
                                output_folder_path=version_path,
                                n_cases=100, n_random_starts=30)

    print("...tuning ended")
