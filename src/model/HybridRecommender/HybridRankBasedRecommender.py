from abc import ABC

import numpy as np

from course_lib.Base.NonPersonalizedRecommender import TopPop
from src.model.HybridRecommender.AbstractHybridRecommender import AbstractHybridRecommender
from typing import Dict, List


class CumulativeScoreBuilder(object):

    def __init__(self):
        self.scores: Dict[int, float] = {}

    def add_score(self, item, score):
        if self.scores.get(item) is None:
            self.scores[item] = score
        else:
            self.scores[item] += score

    def add_scores(self, ranking, scores):
        for item, score in zip(ranking, scores):
            self.add_score(item, score)

    def get_ranking(self, cutoff=None):
        scores_ordered_indices = np.argsort(list(self.scores.values()))[::-1]
        ranking = np.array(list(self.scores.keys()))[scores_ordered_indices]

        if cutoff is None:
            return ranking.tolist()
        else:
            return ranking[:cutoff].tolist()


######## HYBRID STRATEGIES ########

class RecommendationStrategyInterface(ABC):

    def get_hybrid_rankings_and_scores(self, rankings: list, scores: np.ndarray, weight: float):
        """
        Get new rankings and new scores based on the recommendation strategy implemented

        :param rankings: list of each user's ranking of a recommender system
        :param scores: np.ndarray of each user's scores of all items
        :param weight: the weight of a recommender system
        :return:
        """
        raise NotImplementedError("This method has to be implemented by another class")


class WeightedAverageStrategy(RecommendationStrategyInterface):

    def __init__(self, normalize=True):
        self.normalize = normalize

    def get_hybrid_rankings_and_scores(self, rankings: list, scores: np.ndarray, weight: float):
        # min-max normalization
        if self.normalize:
            maximum = np.max(scores, axis=1).reshape((len(scores), 1))

            scores_batch_for_minimum = scores.copy()
            scores_batch_for_minimum[scores_batch_for_minimum == float('-inf')] = np.inf
            minimum = np.min(scores_batch_for_minimum, axis=1).reshape((len(scores), 1))

            denominator = maximum - minimum
            denominator[denominator == 0] = 1.0

            scores = (scores - minimum) / denominator
        # indexing scores by ranking list
        ranking_scores = scores[np.arange(len(rankings)), np.array(rankings, dtype=np.int).T].T
        weighted_scores = weight * ranking_scores
        return rankings, weighted_scores


class WeightedCountStrategy(RecommendationStrategyInterface):

    def get_hybrid_rankings_and_scores(self, rankings: list, scores: np.ndarray, weight: float):
        ranking_scores = np.ones(shape=(len(rankings), len(rankings[0])))
        weighted_scores = np.multiply(ranking_scores, weight)
        return rankings, weighted_scores


class WeightedRankingStrategy(RecommendationStrategyInterface):

    def get_hybrid_rankings_and_scores(self, rankings: list, scores: np.ndarray, weight: float):
        ranking_scores = np.tile(np.arange(1, len(rankings[0]) + 1)[::-1], reps=(len(rankings), 1))
        weighted_scores = np.multiply(ranking_scores, weight)
        return rankings, weighted_scores


class WeightedCountRankingStrategy(RecommendationStrategyInterface):

    def __init__(self, max_value=5):
        self.max_value = max_value

    def get_hybrid_rankings_and_scores(self, rankings: list, scores: np.ndarray, weight: float):
        ranking_scores = np.tile(np.full(shape=len(rankings[0]), fill_value=1), reps=(len(rankings), 1))
        ranking_scores[:, 0] = self.max_value
        weighted_scores = np.multiply(ranking_scores, weight)
        return rankings, weighted_scores


########## Hybrid Recommender ##########

class HybridRankBasedRecommender(AbstractHybridRecommender):
    """
    Hybrid recommender based on rankings of different recommender models: the weighted merge of rankings is done only
    on a specific size of ranking (i.e. cutoff * cutoff_multiplier)
    """

    RECOMMENDER_NAME = "HybridRankBasedRecommender"

    def __init__(self, URM_train):
        super().__init__(URM_train)
        self.hybrid_strategy = None
        self.multiplier_cutoff = None
        self.weights = None
        self.STRATEGY_MAPPER = {"weighted_count": WeightedCountStrategy(), "weighted_rank": WeightedRankingStrategy(),
                                "weighted_count_rank_5": WeightedCountRankingStrategy(5),
                                "weighted_count_rank_3": WeightedCountRankingStrategy(3),
                                "weighted_avg": WeightedAverageStrategy(normalize=False),
                                "norm_weighted_avg": WeightedAverageStrategy(normalize=True)}

    def fit(self, multiplier_cutoff=5, strategy="weighted_avg", **weights):
        """
        Fit the hybrid model by setting the weight of each recommender

        :param strategy: an object of strategy pattern that handles the hybrid core functioning of the recommender
        system
        :param multiplier_cutoff: the multiplier used for multiplying the cutoff for handling more recommended items
        to average
        :param weights: the list of weight of each recommender
        :return: None
        """
        if np.all(np.in1d(weights.keys(), list(self.models.keys()), assume_unique=True)):
            raise ValueError("The weights key name passed does not correspond to the name of the models inside the "
                             "hybrid recommender: {}".format(self.get_recommender_names()))
        if strategy not in self.STRATEGY_MAPPER:
            raise ValueError("The strategy name passed does not correspond to the implemented strategy: "
                             "{}".format(self.STRATEGY_MAPPER))
        self.weights = weights
        self.multiplier_cutoff = multiplier_cutoff
        self.hybrid_strategy = self.STRATEGY_MAPPER[strategy]
        self.sub_recommender = TopPop(URM_train=self.URM_train)
        self.sub_recommender.fit()

    def recommend(self, user_id_array, cutoff=None, remove_seen_flag=True, items_to_compute=None,
                  remove_top_pop_flag=False, remove_custom_items_flag=False, return_scores=False):
        """
        Recommend "number of cutoff" items to a given user_id_array

        REMARK: The RMSE measure got from this hybrid model is incorrect because the score returned is the one from
                last model in the for
        :param user_id_array:
        :param cutoff:
        :param remove_seen_flag:
        :param items_to_compute:
        :param remove_top_pop_flag:
        :param remove_custom_items_flag:
        :param return_scores:
        :return: for each user in user_id_array, a list of recommended items
        """

        # handle user_id_array in case it is scalar
        if np.isscalar(user_id_array):
            user_id_array = np.atleast_1d(user_id_array)
            single_user = True
        else:
            single_user = False

        all_cum_score_builder: List[CumulativeScoreBuilder] = []
        for i in range(len(user_id_array)):
            all_cum_score_builder.append(CumulativeScoreBuilder())

        cutoff_model = cutoff * self.multiplier_cutoff
        scores = []

        sub_rankings = self.sub_recommender.recommend(user_id_array, cutoff=cutoff_model,
                                                      remove_seen_flag=remove_seen_flag,
                                                      items_to_compute=items_to_compute,
                                                      remove_top_pop_flag=remove_top_pop_flag,
                                                      remove_custom_items_flag=remove_custom_items_flag)

        for recommender_name, recommender_model in self.models.items():
            rankings, scores = recommender_model.recommend(user_id_array, cutoff=cutoff_model,
                                                           remove_seen_flag=remove_seen_flag,
                                                           items_to_compute=items_to_compute,
                                                           remove_top_pop_flag=remove_top_pop_flag,
                                                           remove_custom_items_flag=remove_custom_items_flag,
                                                           return_scores=True)

            # Fill empty rankings due to cold users
            for i in range(len(rankings)):
                if len(rankings[i]) == 0:
                    rankings[i] = sub_rankings[i]

            rankings, weighted_scores = self.hybrid_strategy.get_hybrid_rankings_and_scores(rankings=rankings,
                                                                                            scores=scores,
                                                                                            weight=self.weights[
                                                                                                recommender_name])
            for i in range(len(all_cum_score_builder)):
                all_cum_score_builder[i].add_scores(np.array(rankings[i]), np.array(weighted_scores[i]))

        weighted_rankings = [all_cum_score_builder[i].get_ranking(cutoff=cutoff) for i in
                             range(len(all_cum_score_builder))]

        if single_user:
            weighted_rankings = weighted_rankings[0]

        if return_scores:
            return weighted_rankings, scores
        else:
            return weighted_rankings

    def _compute_item_score(self, user_id_array, items_to_compute=None):
        # Useless for this recommender
        pass

    def copy(self):
        copy = HybridRankBasedRecommender(URM_train=self.URM_train)
        copy.models = self.models
        copy.weights = self.weights
        copy.multiplier_cutoff = self.multiplier_cutoff
        return copy

    @classmethod
    def get_possible_strategies(cls):
        return ["weighted_count", "weighted_rank", "weighted_avg", "norm_weighted_avg"]
