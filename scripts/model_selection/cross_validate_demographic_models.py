import os
from datetime import datetime

from course_lib.Base.Evaluation.Evaluator import EvaluatorHoldout
from scripts.model_selection.cross_validate_utils import write_results_on_file, get_seed_list
from scripts.scripts_utils import read_split_load_data
from src.data_management.data_reader import get_UCM_train, get_ignore_users, get_UCM_train_new
from src.model.KNN.UserKNNCBFCFRecommender import UserKNNCBFCFRecommender
from src.model_management.CrossEvaluator import EvaluatorCrossValidationKeepKOut
from src.utils.general_utility_functions import get_project_root_path

# CONSTANTS TO MODIFY
K_OUT = 1
CUTOFF = 10
ALLOW_COLD_USERS = False
LOWER_THRESHOLD = -1  # Remove users below or equal this threshold (default value: -1)
UPPER_THRESHOLD = 22  # Remove users above or equal this threshold (default value: 2**16-1)
IGNORE_NON_TARGET_USERS = True

# VARIABLES TO MODIFY
model_name = "user_cbf_cf"
recommender_class = UserKNNCBFCFRecommender
model_parameters = {'topK': 1050, 'shrink': 151, 'normalize': True, 'interactions_feature_weighting': 'TF-IDF',
                       'similarity': 'cosine', 'feature_weighting': 'TF-IDF'}

if __name__ == '__main__':
    # Set seed in order to have same splitting of data
    seed_list = get_seed_list()
    num_folds = len(seed_list)

    URM_train_list = []
    evaluator_list = []
    UCM_train_list = []
    for i in range(num_folds):
        data_reader = read_split_load_data(K_OUT, ALLOW_COLD_USERS, seed_list[i])
        URM_train, URM_test = data_reader.get_holdout_split()
        UCM_all, _ = get_UCM_train_new(data_reader)

        ignore_users = get_ignore_users(URM_train, data_reader.get_original_user_id_to_index_mapper(),
                                        lower_threshold=LOWER_THRESHOLD, upper_threshold=UPPER_THRESHOLD,
                                        ignore_non_target_users=IGNORE_NON_TARGET_USERS)
        evaluator = EvaluatorHoldout(URM_test, cutoff_list=[CUTOFF], ignore_users=ignore_users)

        URM_train_list.append(URM_train)
        evaluator_list.append(evaluator)
        UCM_train_list.append(UCM_all)

    # Setting evaluator
    evaluator = EvaluatorCrossValidationKeepKOut(URM_train_list, evaluator_list, cutoff=CUTOFF)
    results = evaluator.crossevaluateDemographicRecommender(recommender_class, model_parameters, UCM_train_list)

    # Writing on file cross validation results
    date_string = datetime.now().strftime('%b%d_%H-%M-%S')
    cross_valid_path = os.path.join(get_project_root_path(), "report/cross_validation/")
    file_path = os.path.join(cross_valid_path, "cross_valid_{}_{}.txt".format(model_name, date_string))
    write_results_on_file(file_path, recommender_class.RECOMMENDER_NAME, model_parameters, num_folds, seed_list,
                          results)
