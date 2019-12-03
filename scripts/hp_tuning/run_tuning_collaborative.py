import argparse
from datetime import datetime

from course_lib.Base.Evaluation.Evaluator import *
from course_lib.Data_manager.DataReader_utils import merge_ICM
from course_lib.ParameterTuning.run_parameter_search import *
from src.data_management.New_DataSplitter_leave_k_out import *
from src.data_management.RecSys2019Reader import RecSys2019Reader
from src.data_management.RecSys2019Reader_utils import get_ICM_numerical
from src.utils.general_utility_functions import get_split_seed

N_CASES = 35
N_RANDOM_STARTS = 5
RECOMMENDER_CLASS_DICT = {
    "item_cf": ItemKNNCFRecommender,
    "user_cf": UserKNNCFRecommender,
    "slim_bpr": SLIM_BPR_Cython,
    "p3alpha": P3alphaRecommender,
    "pure_svd": PureSVDRecommender,
    "rp3beta": RP3betaRecommender,
    "asy_svd": MatrixFactorization_AsySVD_Cython,
    "nmf": NMFRecommender,
    "slim_elastic": SLIMElasticNetRecommender,
    "ials": IALSRecommender
}


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--reader_path", default="../../data/", help="path to the root of data files")
    parser.add_argument("-r", "--recommender_name", required=True,
                        help="recommender names should be one of: {}".format(list(RECOMMENDER_CLASS_DICT.keys())))
    parser.add_argument("-n", "--n_cases", default=N_CASES, help="number of cases for hyperparameter tuning")
    parser.add_argument("-nr", "--n_random_starts", default=N_RANDOM_STARTS,
                        help="number of random starts for hyperparameter tuning")
    parser.add_argument("--seed", default=get_split_seed(), help="seed used in splitting the dataset")
    parser.add_argument("-eu", "--exclude_users", default=False, help="1 to exclude cold users, 0 otherwise")

    return parser.parse_args()


def main():
    args = get_arguments()

    # Data loading
    data_reader = RecSys2019Reader(args.reader_path)
    data_reader = New_DataSplitter_leave_k_out(data_reader, k_out_value=3, use_validation_set=False,
                                               force_new_split=True, seed=args.seed)
    data_reader.load_data()
    URM_train, URM_test = data_reader.get_holdout_split()

    # Build ICMs
    ICM_numerical, _ = get_ICM_numerical(data_reader.dataReader_object)
    ICM = data_reader.get_ICM_from_name("ICM_sub_class")
    ICM_all, _ = merge_ICM(ICM, URM_train.transpose(), {}, {})

    # Build UCMs
    URM_all = data_reader.dataReader_object.get_URM_all()
    UCM_age = data_reader.dataReader_object.get_UCM_from_name("UCM_age")
    UCM_region = data_reader.dataReader_object.get_UCM_from_name("UCM_region")

    # Setting evaluator
    exclude_cold_users = args.exclude_users
    if exclude_cold_users:
        print("Excluding cold users...")
        cold_user_mask = np.ediff1d(URM_train.tocsr().indptr) == 0
        ignore_users = np.arange(URM_train.shape[0])[cold_user_mask]
    else:
        ignore_users = None

    cutoff_list = [10]
    evaluator = EvaluatorHoldout(URM_test, cutoff_list=cutoff_list, ignore_users=ignore_users)

    # HP tuning
    print("Start tuning...")
    version_path = "../../report/hp_tuning/{}/".format(args.recommender_name)
    now = datetime.now().strftime('%b%d_%H-%M-%S')
    now = now + "_k_out_value_3/"
    version_path = version_path + "/" + now

    runParameterSearch_Collaborative(URM_train=URM_train,
                                     recommender_class=RECOMMENDER_CLASS_DICT[args.recommender_name],
                                     evaluator_validation=evaluator,
                                     metric_to_optimize="MAP",
                                     output_folder_path=version_path,
                                     n_cases=int(args.n_cases),
                                     n_random_starts=int(args.n_random_starts))
    print("...tuning ended")


if __name__ == '__main__':
    main()
