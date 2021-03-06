from course_lib.Base.BaseRecommender import BaseRecommender
from typing import Dict
import numpy as np


class MapperRecommender(BaseRecommender):

    def __init__(self, URM_train):
        self.main_model: BaseRecommender = None
        self.sub_model: BaseRecommender = None
        self.mapper: Dict = {}
        super().__init__(URM_train)

    def fit(self, main_recommender: BaseRecommender = None, sub_recommender: BaseRecommender = None,
            mapper: Dict = None):
        self.main_model = main_recommender
        self.sub_model = sub_recommender
        self.mapper = mapper

    """def _compute_item_score(self, user_id_array, items_to_compute=None):
        target_original_users = np.array(user_id_array)

        # Building mask
        main_all_original_users = np.array(list(self.mapper.keys()), dtype=np.int32)
        main_all_id_users = np.array(list(self.mapper.values()), dtype=np.int32)
        main_mask = np.in1d(target_original_users, main_all_original_users, assume_unique=True)
        sub_mask = np.logical_not(main_mask)

        # User distinction
        mapper_user_mask = np.in1d(main_all_original_users, target_original_users, assume_unique=True)
        main_users = main_all_id_users[mapper_user_mask]
        sub_users = target_original_users[sub_mask]

        # Computing scores
        main_scores = self.main_model._compute_item_score(user_id_array=main_users, items_to_compute=items_to_compute)
        sub_scores = self.sub_model._compute_item_score(user_id_array=sub_users, items_to_compute=items_to_compute)

        # So far we have to (c, 20k) and (user-id-array-c, 20k) np arrays containing the arrays. Now we
        # have to fix them with the mapper

        # Mixing arrays
        scores = np.empty(shape=(len(user_id_array), self.n_items), dtype=np.float32)

        scores[main_mask, :] = main_scores
        scores[sub_mask, :] = sub_scores

        return scores"""

    def recommend(self, user_id_array, cutoff=None, remove_seen_flag=True, items_to_compute=None,
                  remove_top_pop_flag=False, remove_custom_items_flag=False, return_scores=False):
        if np.isscalar(user_id_array):
            user_id_array = np.atleast_1d(user_id_array)
            single_user = True
        else:
            single_user = False

        target_original_users = np.array(user_id_array)

        # Building mask
        main_all_original_users = np.array(list(self.mapper.keys()), dtype=np.int32)
        main_all_id_users = np.array(list(self.mapper.values()), dtype=np.int32)
        main_mask = np.in1d(target_original_users, main_all_original_users, assume_unique=True)
        sub_mask = np.logical_not(main_mask)

        # User distinction
        mapper_user_mask = np.in1d(main_all_original_users, target_original_users, assume_unique=True)
        main_users = main_all_id_users[mapper_user_mask]
        sub_users = target_original_users[sub_mask]

        main_rankings = self.main_model.recommend(main_users, cutoff=cutoff, remove_seen_flag=remove_seen_flag,
                                                  items_to_compute=items_to_compute,
                                                  remove_top_pop_flag=remove_top_pop_flag,
                                                  remove_custom_items_flag=remove_custom_items_flag,
                                                  return_scores=False)
        sub_rankings = self.sub_model.recommend(sub_users, cutoff=cutoff, remove_seen_flag=remove_seen_flag,
                                                items_to_compute=items_to_compute,
                                                remove_top_pop_flag=remove_top_pop_flag,
                                                remove_custom_items_flag=remove_custom_items_flag,
                                                return_scores=False)
        rankings = np.empty(shape=(len(user_id_array), cutoff), dtype=np.int)
        rankings[main_mask, :] = main_rankings
        rankings[sub_mask, :] = sub_rankings

        if single_user:
            rankings = rankings[0]

        if return_scores:
            return rankings, np.full(shape=(len(user_id_array), self.n_items), fill_value=1)
        else:
            return rankings

    def saveModel(self, folder_path, file_name=None):
        pass
