from course_lib.Base.IR_feature_weighting import TF_IDF
from course_lib.Data_manager.DataReader_utils import merge_ICM
from course_lib.GraphBased.P3alphaRecommender import P3alphaRecommender
from src.data_management.New_DataSplitter_leave_k_out import *
from src.data_management.RecSys2019Reader import RecSys2019Reader
from src.data_management.RecSys2019Reader_utils import get_ICM_numerical, merge_UCM
from src.data_management.data_getter import get_warmer_UCM
from src.data_management.data_reader import get_ICM_train, get_UCM_train
from src.feature.demographics_content import get_user_demographic
from src.model import best_models, new_best_models
from src.model.KNN.ItemKNNCBFCFRecommender import ItemKNNCBFCFRecommender
from src.plots.recommender_plots import *
from src.utils.general_utility_functions import get_split_seed

if __name__ == '__main__':
    root_data_path = "../../data"
    k_out = 3
    data_reader = RecSys2019Reader(root_data_path)
    data_reader = New_DataSplitter_leave_k_out(data_reader, k_out_value=k_out, use_validation_set=False,
                                               force_new_split=True, seed=get_split_seed())
    data_reader.load_data()
    URM_train, URM_test = data_reader.get_holdout_split()

    ICM_all_new = get_ICM_train(data_reader)

    UCM_all_new = get_UCM_train(data_reader, root_data_path)

    # Build ICMs
    ICM_numerical, _ = get_ICM_numerical(data_reader.dataReader_object)
    ICM = data_reader.get_ICM_from_name("ICM_all")
    ICM_subclass = data_reader.get_ICM_from_name("ICM_sub_class")

    # Build UCMs
    URM_all = data_reader.dataReader_object.get_URM_all()
    UCM_age = data_reader.dataReader_object.get_UCM_from_name("UCM_age")
    UCM_region = data_reader.dataReader_object.get_UCM_from_name("UCM_region")
    UCM_age_region, _ = merge_UCM(UCM_age, UCM_region, {}, {})

    UCM_age_region = get_warmer_UCM(UCM_age_region, URM_all, threshold_users=k_out)

    UCM_region_warm = get_warmer_UCM(UCM_region, URM_all, threshold_users=k_out)
    UCM_age_warm = get_warmer_UCM(UCM_age, URM_all, threshold_users=k_out)

    #fusion = new_best_models.FusionMergeItem_CBF_CF.get_model(URM_train, ICM_all_new)
    #sub2 = best_models.HybridWeightedAvgSubmission2.get_model(URM_train=URM_train, ICM_train=ICM_subclass,
    #                                                          UCM_train=UCM_age_region)
    #sub2.RECOMMENDER_NAME = "SUB2"

    #mixed = best_models.WeightedAverageMixed.get_model(URM_train=URM_train, ICM_subclass=ICM_subclass,
    #                                                  ICM_all=ICM, UCM_age_region=UCM_age_region)
    #mixed.RECOMMENDER_NAME = "MIXED"

    item_cbf_cf = new_best_models.ItemCBF_CF.get_model(URM_train, ICM_all_new)
    #user_cbf_cf = new_best_models.UserCBF_CF_Warm.get_model(URM_train, UCM_all_new)

    recommender_list = [item_cbf_cf]

    for value in [400, 450, 500, 550]:
        # warm_users_mask = np.ediff1d(URM_train.tocsr().indptr) > value
        # warm_users = np.arange(URM_train.shape[0])[warm_users_mask]
        warm_items_mask = np.ediff1d(URM_train.tocsc().indptr) > value
        warm_items = np.arange(URM_train.shape[1])[warm_items_mask]
        URM_train_new = URM_train.copy().tolil()
        URM_train_new[:, warm_items] = 0
        URM_train_new = URM_train_new.tocsr()
        URM_train_new.eliminate_zeros()
        print(len(warm_items))
        par = new_best_models.ItemCBF_CF.get_best_parameters()
        model = ItemKNNCBFCFRecommender(URM_train_new, ICM_all_new)
        model.RECOMMENDER_NAME = "ItemKNNCBFCF_delete_items_{}".format(value)
        model.fit(**par)
        model.URM_train = URM_train
        recommender_list.append(model)

    # Building path
    version_path = "../../report/graphics/comparison/"

    # Plot the comparison on item popularity
    """item_popularity, item_popularity_descriptor = get_profile_demographic_wrapper(URM_train, bins=10, users=False)
    content_plot(recommender_instance_list=recommender_list, URM_train=URM_train,
                 URM_test=URM_test, cutoff=10, metric="MAP", save_on_file=True,
                 output_folder_path=version_path + "item_popularity/", content_name="Item popularity",
                 content=item_popularity, content_describer_list=item_popularity_descriptor,
                 exclude_cold_items=False)"""

    # Plotting the comparison on age
    region_demographic = get_user_demographic(UCM_region_warm, URM_train, 1, binned=True)
    region_demographic_describer_list = [-1, 0, 2, 3, 4, 5, 6, 7]
    demographic_plot(recommender_instance_list=recommender_list, URM_train=URM_train,
                     URM_test=URM_test, cutoff=10, metric="MAP", save_on_file=True,
                     output_folder_path=version_path + "region/", demographic_name="Region",
                     demographic=region_demographic, demographic_describer_list=region_demographic_describer_list,
                     exclude_cold_users=True)

    # Plotting the comparison on region
    age_demographic = get_user_demographic(UCM_age, URM_all, 1, binned=True)
    age_demographic_describer_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    demographic_plot(recommender_instance_list=recommender_list, URM_train=URM_train,
                     URM_test=URM_test, cutoff=10, metric="MAP", save_on_file=True,
                     output_folder_path=version_path + "age/", demographic_name="Age",
                     demographic=age_demographic, demographic_describer_list=age_demographic_describer_list,
                     exclude_cold_users=True)

    # Plot on profile lenght
    plot_compare_recommenders_user_profile_len(recommender_list, URM_train, URM_test, save_on_file=True,
                                               output_folder_path=version_path + "user_activity/",
                                               bins=30)

    # Plotting the comparison based on clustering
    # dataframe = get_preprocessed_dataframe(path="../../data/", keep_warm_only=True)
    # plot_clustering_demographics(recommender_list, URM_train, URM_test, dataframe,
    #                             metric="MAP", cutoff=10, save_on_file=True,
    #                             output_folder_path=version_path + "clustering/",
    #                             exclude_cold_users=True, n_clusters=25,
    #                             n_init=10)
